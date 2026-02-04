import json
import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import RiskLevel, StratificationMetric
from app.models.stratification import StratificationConfig, StratificationResult
from app.models.user import User
from app.schemas.stratification import (
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    GeoJSONGeometry,
    GeoJSONProperties,
    StratificationConfigCreate,
    StratificationConfigResponse,
    StratificationConfigUpdate,
    StratificationResultResponse,
    StratificationSummaryResponse,
)


class StratificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_config(
        self,
        project_id: uuid.UUID,
        data: StratificationConfigCreate,
        user: User,
    ) -> StratificationConfigResponse:
        config = StratificationConfig(
            project_id=project_id,
            name=data.name,
            metric=data.metric.value,
            thresholds={
                k: {"min_value": v.min_value, "max_value": v.max_value}
                for k, v in data.thresholds.items()
            },
            created_by=user.id,
        )
        self.db.add(config)
        await self.db.flush()
        return StratificationConfigResponse.model_validate(config)

    async def list_configs(
        self, project_id: uuid.UUID
    ) -> list[StratificationConfigResponse]:
        result = await self.db.execute(
            select(StratificationConfig)
            .where(StratificationConfig.project_id == project_id)
            .order_by(StratificationConfig.created_at.desc())
        )
        configs = result.scalars().all()
        return [StratificationConfigResponse.model_validate(c) for c in configs]

    async def update_config(
        self, config_id: uuid.UUID, data: StratificationConfigUpdate
    ) -> StratificationConfigResponse:
        result = await self.db.execute(
            select(StratificationConfig).where(
                StratificationConfig.id == config_id
            )
        )
        config = result.scalar_one_or_none()
        if config is None:
            raise ValueError("Stratification config not found")

        if data.name is not None:
            config.name = data.name
        if data.thresholds is not None:
            config.thresholds = {
                k: {"min_value": v.min_value, "max_value": v.max_value}
                for k, v in data.thresholds.items()
            }
        if data.is_active is not None:
            config.is_active = data.is_active

        await self.db.flush()
        return StratificationConfigResponse.model_validate(config)

    async def calculate_stratification(
        self,
        config_id: uuid.UUID,
        data: list[dict],
    ) -> list[StratificationResultResponse]:
        """
        Calculate stratification from provided data.

        Each item in `data` should have:
        - admin_unit_name: str
        - admin_unit_code: str (optional)
        - metric_value: float (PfPR, incidence, or EIR)
        - population: int (optional)
        - cases_annual: int (optional)
        - deaths_annual: int (optional)
        - geometry: GeoJSON geometry dict (optional)
        """
        result = await self.db.execute(
            select(StratificationConfig).where(
                StratificationConfig.id == config_id
            )
        )
        config = result.scalar_one_or_none()
        if config is None:
            raise ValueError("Stratification config not found")

        # Delete previous results for this config
        await self.db.execute(
            delete(StratificationResult).where(
                StratificationResult.config_id == config_id
            )
        )

        thresholds = config.thresholds
        results = []

        for item in data:
            metric_value = item["metric_value"]
            risk_level = self._assign_risk_level(metric_value, thresholds)
            eligible = self._determine_eligible_interventions(
                risk_level, StratificationMetric(config.metric), item
            )

            strat_result = StratificationResult(
                config_id=config_id,
                admin_unit_name=item["admin_unit_name"],
                admin_unit_code=item.get("admin_unit_code"),
                metric_value=metric_value,
                risk_level=risk_level.value,
                eligible_interventions={"interventions": eligible},
                population=item.get("population"),
                cases_annual=item.get("cases_annual"),
                deaths_annual=item.get("deaths_annual"),
            )
            self.db.add(strat_result)
            results.append(strat_result)

        await self.db.flush()
        return [StratificationResultResponse.model_validate(r) for r in results]

    async def get_results(
        self, config_id: uuid.UUID
    ) -> list[StratificationResultResponse]:
        result = await self.db.execute(
            select(StratificationResult)
            .where(StratificationResult.config_id == config_id)
            .order_by(StratificationResult.admin_unit_name)
        )
        results = result.scalars().all()
        return [StratificationResultResponse.model_validate(r) for r in results]

    async def get_geojson(self, config_id: uuid.UUID) -> GeoJSONFeatureCollection:
        """Generate GeoJSON for map visualization."""
        result = await self.db.execute(
            select(StratificationResult).where(
                StratificationResult.config_id == config_id
            )
        )
        results = result.scalars().all()

        features = []
        for r in results:
            # Get geometry as GeoJSON if PostGIS geometry exists
            geometry = None
            if r.geometry is not None:
                geojson_str = await self.db.scalar(
                    func.ST_AsGeoJSON(r.geometry)
                )
                if geojson_str:
                    geometry = GeoJSONGeometry(**json.loads(geojson_str))

            interventions = None
            if r.eligible_interventions:
                interventions = r.eligible_interventions.get("interventions")

            feature = GeoJSONFeature(
                geometry=geometry,
                properties=GeoJSONProperties(
                    unit_id=r.id,
                    unit_name=r.admin_unit_name,
                    unit_code=r.admin_unit_code,
                    risk_level=RiskLevel(r.risk_level),
                    metric_value=r.metric_value,
                    population=r.population,
                    cases_annual=r.cases_annual,
                    deaths_annual=r.deaths_annual,
                    eligible_interventions=interventions,
                ),
            )
            features.append(feature)

        return GeoJSONFeatureCollection(features=features)

    async def get_summary(
        self, config_id: uuid.UUID
    ) -> StratificationSummaryResponse:
        """Get summary statistics for stratification results."""
        result = await self.db.execute(
            select(StratificationConfig).where(
                StratificationConfig.id == config_id
            )
        )
        config = result.scalar_one_or_none()
        if config is None:
            raise ValueError("Config not found")

        results_query = await self.db.execute(
            select(StratificationResult).where(
                StratificationResult.config_id == config_id
            )
        )
        results = results_query.scalars().all()

        risk_dist: dict[str, int] = {}
        total_pop = 0
        total_cases = 0

        for r in results:
            risk_dist[r.risk_level] = risk_dist.get(r.risk_level, 0) + 1
            if r.population:
                total_pop += r.population
            if r.cases_annual:
                total_cases += r.cases_annual

        return StratificationSummaryResponse(
            config_id=config.id,
            config_name=config.name,
            metric=StratificationMetric(config.metric),
            total_units=len(results),
            risk_distribution=risk_dist,
            total_population=total_pop,
            total_cases=total_cases,
        )

    def _assign_risk_level(
        self, metric_value: float, thresholds: dict
    ) -> RiskLevel:
        """Assign risk level based on threshold ranges."""
        # Thresholds format: {"very_low": {"min_value": 0, "max_value": 1}, ...}
        for level_name in ["very_low", "low", "moderate", "high"]:
            if level_name in thresholds:
                t = thresholds[level_name]
                if t["min_value"] <= metric_value < t["max_value"]:
                    return RiskLevel(level_name)

        # Default to high if above all thresholds
        return RiskLevel.HIGH

    def _determine_eligible_interventions(
        self,
        risk_level: RiskLevel,
        metric: StratificationMetric,
        unit_data: dict,
    ) -> list[str]:
        """Determine eligible interventions based on WHO guidelines."""
        eligible = []

        # Case management - universal
        eligible.append("CM")

        if risk_level in (RiskLevel.LOW, RiskLevel.MODERATE, RiskLevel.HIGH):
            eligible.append("ITN")

        if risk_level in (RiskLevel.MODERATE, RiskLevel.HIGH):
            eligible.append("IRS")

        if risk_level != RiskLevel.VERY_LOW:
            eligible.append("IPTp")

        if risk_level in (RiskLevel.MODERATE, RiskLevel.HIGH):
            eligible.append("SMC")
            eligible.append("VACCINE")

        return eligible

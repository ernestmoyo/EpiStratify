"""Impact forecasting using simplified transmission model."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ForecastStatus
from app.models.intervention import ForecastResult, InterventionScenario
from app.schemas.forecast import (
    ForecastComparisonResponse,
    ForecastRequest,
    ForecastResultResponse,
    ForecastSummaryResponse,
)

# Intervention effectiveness parameters (proportion reduction in cases)
INTERVENTION_EFFECTIVENESS = {
    "itn": {"cases_reduction": 0.50, "deaths_reduction": 0.55},
    "irs": {"cases_reduction": 0.45, "deaths_reduction": 0.50},
    "smc": {"cases_reduction": 0.75, "deaths_reduction": 0.75},  # Among target group
    "iptp": {"cases_reduction": 0.10, "deaths_reduction": 0.15},
    "vaccine": {"cases_reduction": 0.40, "deaths_reduction": 0.45},
    "cm": {"cases_reduction": 0.20, "deaths_reduction": 0.60},
    "pmc": {"cases_reduction": 0.30, "deaths_reduction": 0.35},
    "lsm": {"cases_reduction": 0.10, "deaths_reduction": 0.08},
}


class ForecastService:
    """Impact forecasting for intervention scenarios."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_forecast(
        self,
        scenario_id: uuid.UUID,
        request: ForecastRequest,
        baseline_data: dict[str, Any] | None = None,
    ) -> ForecastResultResponse:
        """
        Run impact forecast for a scenario.

        baseline_data should include:
        - baseline_cases: int (annual baseline cases)
        - baseline_deaths: int (annual baseline deaths)
        - baseline_prevalence: float (PfPR %)
        - population: int
        """
        result = await self.db.execute(
            select(InterventionScenario).where(
                InterventionScenario.id == scenario_id
            )
        )
        scenario = result.scalar_one_or_none()
        if scenario is None:
            raise ValueError("Scenario not found")

        baseline = baseline_data or {}
        baseline_cases = baseline.get("baseline_cases", 100000)
        baseline_deaths = baseline.get("baseline_deaths", 500)
        baseline_prev = baseline.get("baseline_prevalence", 15.0)
        population = baseline.get("population", 1000000)
        years = request.projection_years

        if request.model_type == "simple":
            forecast_data = self._simple_forecast(
                scenario=scenario,
                baseline_cases=baseline_cases,
                baseline_deaths=baseline_deaths,
                baseline_prevalence=baseline_prev,
                population=population,
                years=years,
            )
        else:
            # For external models, create a pending record
            forecast_data = {
                "status": ForecastStatus.PENDING.value,
                "projected_cases": None,
                "projected_deaths": None,
                "projected_prevalence": None,
                "cases_averted": None,
                "deaths_averted": None,
            }

        # Calculate cost-effectiveness if cost data available
        cost_per_case = None
        cost_per_death = None
        cost_per_daly = None

        if scenario.total_cost and forecast_data.get("cases_averted"):
            cases_averted = forecast_data["cases_averted"]
            deaths_averted = forecast_data.get("deaths_averted", 0)
            dalys = forecast_data.get("dalys_averted", 0)

            if cases_averted > 0:
                cost_per_case = scenario.total_cost / cases_averted
            if deaths_averted > 0:
                cost_per_death = scenario.total_cost / deaths_averted
            if dalys > 0:
                cost_per_daly = scenario.total_cost / dalys

        forecast = ForecastResult(
            scenario_id=scenario_id,
            status=forecast_data.get("status", ForecastStatus.COMPLETED.value),
            model_type=request.model_type,
            projected_cases=forecast_data.get("projected_cases"),
            projected_deaths=forecast_data.get("projected_deaths"),
            projected_prevalence=forecast_data.get("projected_prevalence"),
            cases_averted=forecast_data.get("cases_averted"),
            deaths_averted=forecast_data.get("deaths_averted"),
            dalys_averted=forecast_data.get("dalys_averted"),
            cost_per_case_averted=cost_per_case,
            cost_per_death_averted=cost_per_death,
            cost_per_daly_averted=cost_per_daly,
            uncertainty_bounds=forecast_data.get("uncertainty"),
            parameters={
                "baseline": baseline,
                "model_type": request.model_type,
                "projection_years": years,
            },
        )
        self.db.add(forecast)

        # Update scenario with aggregate results
        scenario.estimated_cases_averted = forecast_data.get("cases_averted")
        scenario.estimated_deaths_averted = forecast_data.get("deaths_averted")

        await self.db.flush()
        return ForecastResultResponse.model_validate(forecast)

    async def get_forecast(
        self, forecast_id: uuid.UUID
    ) -> ForecastResultResponse:
        result = await self.db.execute(
            select(ForecastResult).where(ForecastResult.id == forecast_id)
        )
        forecast = result.scalar_one_or_none()
        if forecast is None:
            raise ValueError("Forecast not found")
        return ForecastResultResponse.model_validate(forecast)

    async def list_forecasts(
        self, scenario_id: uuid.UUID
    ) -> list[ForecastResultResponse]:
        result = await self.db.execute(
            select(ForecastResult)
            .where(ForecastResult.scenario_id == scenario_id)
            .order_by(ForecastResult.created_at.desc())
        )
        forecasts = result.scalars().all()
        return [ForecastResultResponse.model_validate(f) for f in forecasts]

    async def compare_forecasts(
        self, project_id: uuid.UUID
    ) -> ForecastComparisonResponse:
        """Compare forecasts across all scenarios in a project."""
        result = await self.db.execute(
            select(InterventionScenario).where(
                InterventionScenario.project_id == project_id
            )
        )
        scenarios = result.scalars().all()

        summaries = []
        best_cases_id = None
        best_cases_count = 0
        best_ce_id = None
        best_ce_ratio = float("inf")

        for scenario in scenarios:
            # Get latest forecast
            fr = await self.db.execute(
                select(ForecastResult)
                .where(
                    ForecastResult.scenario_id == scenario.id,
                    ForecastResult.status == ForecastStatus.COMPLETED.value,
                )
                .order_by(ForecastResult.created_at.desc())
                .limit(1)
            )
            forecast = fr.scalar_one_or_none()

            cases_averted = forecast.cases_averted if forecast else None
            deaths_averted = forecast.deaths_averted if forecast else None
            final_year_cases = None
            final_year_deaths = None

            if forecast and forecast.projected_cases:
                years = sorted(forecast.projected_cases.keys())
                if years:
                    final_year_cases = forecast.projected_cases[years[-1]]
            if forecast and forecast.projected_deaths:
                years = sorted(forecast.projected_deaths.keys())
                if years:
                    final_year_deaths = forecast.projected_deaths[years[-1]]

            summary = ForecastSummaryResponse(
                scenario_id=scenario.id,
                scenario_name=scenario.name,
                baseline_cases=forecast.parameters.get("baseline", {}).get("baseline_cases", 0) if forecast and forecast.parameters else 0,
                baseline_deaths=forecast.parameters.get("baseline", {}).get("baseline_deaths", 0) if forecast and forecast.parameters else 0,
                projected_cases_final_year=final_year_cases,
                projected_deaths_final_year=final_year_deaths,
                total_cases_averted=cases_averted,
                total_deaths_averted=deaths_averted,
                cost_effectiveness={
                    "cost_per_case_averted": forecast.cost_per_case_averted if forecast else None,
                    "cost_per_death_averted": forecast.cost_per_death_averted if forecast else None,
                },
            )
            summaries.append(summary)

            # Track best
            if cases_averted and cases_averted > best_cases_count:
                best_cases_count = cases_averted
                best_cases_id = scenario.id
            if forecast and forecast.cost_per_case_averted:
                if forecast.cost_per_case_averted < best_ce_ratio:
                    best_ce_ratio = forecast.cost_per_case_averted
                    best_ce_id = scenario.id

        return ForecastComparisonResponse(
            scenarios=summaries,
            best_by_cases_averted=best_cases_id,
            best_by_cost_effectiveness=best_ce_id,
        )

    def _simple_forecast(
        self,
        scenario: InterventionScenario,
        baseline_cases: int,
        baseline_deaths: int,
        baseline_prevalence: float,
        population: int,
        years: int,
    ) -> dict:
        """
        Simplified transmission model for impact forecasting.

        Assumes interventions reduce cases/deaths by a combined effectiveness
        factor, with diminishing returns when multiple interventions overlap.
        """
        # Calculate combined effectiveness across all units
        all_interventions: set[str] = set()
        for unit_interventions in scenario.interventions.values():
            all_interventions.update(unit_interventions)

        # Combined effectiveness (with diminishing returns)
        combined_case_reduction = 0.0
        combined_death_reduction = 0.0

        for intervention in sorted(all_interventions):
            eff = INTERVENTION_EFFECTIVENESS.get(intervention, {})
            case_eff = eff.get("cases_reduction", 0)
            death_eff = eff.get("deaths_reduction", 0)

            # Diminishing returns: each additional intervention acts on remaining cases
            combined_case_reduction = (
                combined_case_reduction + (1 - combined_case_reduction) * case_eff
            )
            combined_death_reduction = (
                combined_death_reduction + (1 - combined_death_reduction) * death_eff
            )

        # Cap at 95% reduction
        combined_case_reduction = min(combined_case_reduction, 0.95)
        combined_death_reduction = min(combined_death_reduction, 0.95)

        # Project year by year with gradual scale-up
        projected_cases = {}
        projected_deaths = {}
        projected_prevalence = {}
        total_cases_averted = 0
        total_deaths_averted = 0
        base_year = 2025

        for y in range(years):
            year = base_year + y
            # Scale-up factor: 50% year 1, 75% year 2, 100% year 3+
            scale_up = min(1.0, 0.5 + (y * 0.25))
            effective_case_reduction = combined_case_reduction * scale_up
            effective_death_reduction = combined_death_reduction * scale_up

            year_cases = int(baseline_cases * (1 - effective_case_reduction))
            year_deaths = int(baseline_deaths * (1 - effective_death_reduction))
            year_prevalence = round(
                baseline_prevalence * (1 - effective_case_reduction * 0.8), 2
            )

            projected_cases[str(year)] = year_cases
            projected_deaths[str(year)] = year_deaths
            projected_prevalence[str(year)] = year_prevalence

            total_cases_averted += baseline_cases - year_cases
            total_deaths_averted += baseline_deaths - year_deaths

        # DALY estimate: ~0.02 DALYs per case + 30 DALYs per death
        dalys_averted = total_cases_averted * 0.02 + total_deaths_averted * 30

        # Uncertainty bounds (simplified +/- 20%)
        uncertainty = {
            "cases_averted": {
                "lower": int(total_cases_averted * 0.8),
                "upper": int(total_cases_averted * 1.2),
            },
            "deaths_averted": {
                "lower": int(total_deaths_averted * 0.8),
                "upper": int(total_deaths_averted * 1.2),
            },
        }

        return {
            "status": ForecastStatus.COMPLETED.value,
            "projected_cases": projected_cases,
            "projected_deaths": projected_deaths,
            "projected_prevalence": projected_prevalence,
            "cases_averted": total_cases_averted,
            "deaths_averted": total_deaths_averted,
            "dalys_averted": round(dalys_averted, 1),
            "uncertainty": uncertainty,
        }

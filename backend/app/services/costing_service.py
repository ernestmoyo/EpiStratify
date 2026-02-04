"""Budget scenario planning and costing (Annex 8)."""

import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import InterventionCode, ScenarioType
from app.models.intervention import InterventionScenario, ScenarioCostItem
from app.models.user import User
from app.schemas.intervention import (
    ScenarioCostItemResponse,
    ScenarioCostSummary,
    ScenarioComparisonResponse,
    ScenarioCreate,
    ScenarioDetailResponse,
    ScenarioResponse,
    ScenarioUpdate,
)

# Default unit costs (USD) — can be overridden per country
DEFAULT_UNIT_COSTS = {
    "itn": {
        "procurement": 2.50,       # Per net
        "distribution": 1.50,      # Per net
        "bcc_annual": 0.10,        # Per capita per year
        "nets_per_capita": 0.5,    # 1 net per 2 people
        "replacement_years": 3,    # LLIN lifespan
    },
    "irs": {
        "insecticide_per_structure": 5.00,
        "operations_per_structure": 3.50,
        "mobilization_per_capita": 0.20,
        "persons_per_structure": 5,
    },
    "smc": {
        "drugs_per_child_per_cycle": 0.50,
        "delivery_per_child_per_cycle": 0.80,
        "default_cycles": 4,
        "under5_proportion": 0.18,
    },
    "iptp": {
        "drugs_per_pregnant_woman": 0.30,
        "delivery_per_visit": 0.50,
        "pregnant_proportion": 0.04,
        "visits_per_pregnancy": 4,
    },
    "vaccine": {
        "vaccine_per_dose": 2.00,
        "delivery_per_dose": 1.50,
        "doses_per_child": 4,
        "target_proportion": 0.03,  # Children in eligible age range
    },
    "cm": {
        "rdt_per_test": 0.50,
        "act_per_treatment": 1.20,
        "test_rate": 0.15,          # Tests per capita per year
        "positivity_rate": 0.30,
    },
    "pmc": {
        "drugs_per_infant_per_dose": 0.40,
        "delivery_per_dose": 0.50,
        "doses": 3,
        "infant_proportion": 0.03,
    },
    "lsm": {
        "cost_per_hectare_per_year": 150.00,
        "hectares_per_1000_pop": 0.5,
    },
}


class CostingService:
    """Budget planning and scenario cost analysis."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_scenario(
        self,
        project_id: uuid.UUID,
        data: ScenarioCreate,
        user: User,
    ) -> ScenarioResponse:
        scenario = InterventionScenario(
            project_id=project_id,
            name=data.name,
            description=data.description,
            scenario_type=data.scenario_type.value,
            interventions=data.interventions,
            created_by=user.id,
        )
        self.db.add(scenario)
        await self.db.flush()
        return ScenarioResponse.model_validate(scenario)

    async def list_scenarios(
        self, project_id: uuid.UUID
    ) -> list[ScenarioResponse]:
        result = await self.db.execute(
            select(InterventionScenario)
            .where(InterventionScenario.project_id == project_id)
            .order_by(InterventionScenario.created_at.desc())
        )
        scenarios = result.scalars().all()
        return [ScenarioResponse.model_validate(s) for s in scenarios]

    async def get_scenario(
        self, scenario_id: uuid.UUID
    ) -> ScenarioDetailResponse:
        result = await self.db.execute(
            select(InterventionScenario).where(
                InterventionScenario.id == scenario_id
            )
        )
        scenario = result.scalar_one_or_none()
        if scenario is None:
            raise ValueError("Scenario not found")

        cost_result = await self.db.execute(
            select(ScenarioCostItem)
            .where(ScenarioCostItem.scenario_id == scenario_id)
            .order_by(ScenarioCostItem.admin_unit_name)
        )
        cost_items = cost_result.scalars().all()

        return ScenarioDetailResponse(
            id=scenario.id,
            name=scenario.name,
            description=scenario.description,
            scenario_type=ScenarioType(scenario.scenario_type),
            is_selected=scenario.is_selected,
            interventions=scenario.interventions,
            total_cost=scenario.total_cost,
            population_covered=scenario.population_covered,
            estimated_cases_averted=scenario.estimated_cases_averted,
            estimated_deaths_averted=scenario.estimated_deaths_averted,
            created_at=scenario.created_at,
            cost_items=[ScenarioCostItemResponse.model_validate(c) for c in cost_items],
        )

    async def update_scenario(
        self, scenario_id: uuid.UUID, data: ScenarioUpdate
    ) -> ScenarioResponse:
        result = await self.db.execute(
            select(InterventionScenario).where(
                InterventionScenario.id == scenario_id
            )
        )
        scenario = result.scalar_one_or_none()
        if scenario is None:
            raise ValueError("Scenario not found")

        if data.name is not None:
            scenario.name = data.name
        if data.description is not None:
            scenario.description = data.description
        if data.interventions is not None:
            scenario.interventions = data.interventions
        if data.is_selected is not None:
            scenario.is_selected = data.is_selected

        await self.db.flush()
        return ScenarioResponse.model_validate(scenario)

    async def delete_scenario(self, scenario_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(InterventionScenario).where(
                InterventionScenario.id == scenario_id
            )
        )
        scenario = result.scalar_one_or_none()
        if scenario is None:
            raise ValueError("Scenario not found")
        await self.db.delete(scenario)

    async def calculate_scenario_cost(
        self,
        scenario_id: uuid.UUID,
        population_data: list[dict[str, Any]],
        unit_costs: dict | None = None,
        project_years: int = 5,
    ) -> ScenarioCostSummary:
        """
        Calculate costs for all interventions in a scenario.

        population_data: list of {"admin_unit_name": str, "admin_unit_code": str, "population": int}
        unit_costs: optional override for default costs
        """
        result = await self.db.execute(
            select(InterventionScenario).where(
                InterventionScenario.id == scenario_id
            )
        )
        scenario = result.scalar_one_or_none()
        if scenario is None:
            raise ValueError("Scenario not found")

        costs = unit_costs or DEFAULT_UNIT_COSTS

        # Delete previous cost items
        await self.db.execute(
            delete(ScenarioCostItem).where(
                ScenarioCostItem.scenario_id == scenario_id
            )
        )

        pop_map = {
            item.get("admin_unit_code", item["admin_unit_name"]): item
            for item in population_data
        }

        total_cost = 0.0
        total_population = 0
        cost_by_intervention: dict[str, float] = {}
        cost_by_unit: dict[str, float] = {}

        for unit_key, interventions in scenario.interventions.items():
            unit_info = pop_map.get(unit_key, {})
            population = unit_info.get("population", 0)
            unit_name = unit_info.get("admin_unit_name", unit_key)
            total_population += population

            unit_total = 0.0

            for intervention_str in interventions:
                intervention_cost = self._calculate_intervention_cost(
                    intervention_str, population, costs, project_years
                )

                cost_item = ScenarioCostItem(
                    scenario_id=scenario_id,
                    admin_unit_name=unit_name,
                    admin_unit_code=unit_key,
                    intervention_code=intervention_str,
                    total_cost=intervention_cost,
                    years=project_years,
                    cost_details={
                        "population": population,
                        "unit_costs": costs.get(intervention_str, {}),
                    },
                )
                self.db.add(cost_item)

                total_cost += intervention_cost
                unit_total += intervention_cost
                cost_by_intervention[intervention_str] = (
                    cost_by_intervention.get(intervention_str, 0) + intervention_cost
                )

            cost_by_unit[unit_key] = unit_total

        # Update scenario totals
        scenario.total_cost = total_cost
        scenario.population_covered = total_population

        await self.db.flush()

        return ScenarioCostSummary(
            scenario_id=scenario_id,
            scenario_name=scenario.name,
            total_cost=total_cost,
            cost_by_intervention=cost_by_intervention,
            cost_by_unit=cost_by_unit,
            cost_per_capita=(
                total_cost / total_population if total_population > 0 else None
            ),
            total_population=total_population,
        )

    async def compare_scenarios(
        self, project_id: uuid.UUID
    ) -> ScenarioComparisonResponse:
        """Compare all scenarios for a project."""
        scenarios = await self.list_scenarios(project_id)

        comparison: dict[str, dict[str, Any]] = {}
        for s in scenarios:
            comparison[str(s.id)] = {
                "name": s.name,
                "total_cost": s.total_cost or 0,
                "population_covered": s.population_covered or 0,
                "cases_averted": s.estimated_cases_averted or 0,
                "deaths_averted": s.estimated_deaths_averted or 0,
                "cost_per_case_averted": (
                    (s.total_cost / s.estimated_cases_averted)
                    if s.total_cost and s.estimated_cases_averted
                    else None
                ),
            }

        return ScenarioComparisonResponse(
            scenarios=scenarios,
            comparison_metrics=comparison,
        )

    async def optimize_scenario(
        self,
        scenario_id: uuid.UUID,
        budget_constraint: float,
        population_data: list[dict],
    ) -> ScenarioResponse:
        """
        Optimize a scenario under a budget constraint.
        Uses a greedy approach based on cost-effectiveness.
        """
        result = await self.db.execute(
            select(InterventionScenario).where(
                InterventionScenario.id == scenario_id
            )
        )
        scenario = result.scalar_one_or_none()
        if scenario is None:
            raise ValueError("Scenario not found")

        pop_map = {
            item.get("admin_unit_code", item["admin_unit_name"]): item
            for item in population_data
        }

        # Calculate cost-effectiveness for each unit-intervention pair
        ce_data = []
        for unit_key, interventions in scenario.interventions.items():
            unit_info = pop_map.get(unit_key, {})
            population = unit_info.get("population", 0)

            for intervention in interventions:
                cost = self._calculate_intervention_cost(
                    intervention, population, DEFAULT_UNIT_COSTS, 5
                )
                # Simplified effect estimate based on population and intervention type
                effect = self._estimate_effect(intervention, population)
                icer = cost / effect if effect > 0 else float("inf")

                ce_data.append({
                    "unit_key": unit_key,
                    "intervention": intervention,
                    "cost": cost,
                    "effect": effect,
                    "icer": icer,
                })

        # Sort by ICER (ascending = most cost-effective first)
        ce_data.sort(key=lambda x: x["icer"])

        # Select until budget exhausted
        optimized: dict[str, list[str]] = {}
        running_cost = 0.0

        for item in ce_data:
            if running_cost + item["cost"] <= budget_constraint:
                if item["unit_key"] not in optimized:
                    optimized[item["unit_key"]] = []
                optimized[item["unit_key"]].append(item["intervention"])
                running_cost += item["cost"]

        scenario.interventions = optimized
        scenario.total_cost = running_cost
        await self.db.flush()

        return ScenarioResponse.model_validate(scenario)

    def _calculate_intervention_cost(
        self,
        intervention: str,
        population: int,
        costs: dict,
        years: int,
    ) -> float:
        """Calculate cost for a single intervention in a single unit."""
        ic = costs.get(intervention, {})

        if intervention == "itn":
            nets = population * ic.get("nets_per_capita", 0.5)
            replacement = ic.get("replacement_years", 3)
            cycles = years / replacement
            return (
                nets * ic.get("procurement", 2.5) * cycles
                + nets * ic.get("distribution", 1.5) * cycles
                + population * ic.get("bcc_annual", 0.1) * years
            )

        elif intervention == "irs":
            structures = population / ic.get("persons_per_structure", 5)
            return (
                structures * ic.get("insecticide_per_structure", 5) * years
                + structures * ic.get("operations_per_structure", 3.5) * years
                + population * ic.get("mobilization_per_capita", 0.2) * years
            )

        elif intervention == "smc":
            target = population * ic.get("under5_proportion", 0.18)
            cycles = ic.get("default_cycles", 4)
            return (
                target * ic.get("drugs_per_child_per_cycle", 0.5) * cycles * years
                + target * ic.get("delivery_per_child_per_cycle", 0.8) * cycles * years
            )

        elif intervention == "iptp":
            target = population * ic.get("pregnant_proportion", 0.04)
            visits = ic.get("visits_per_pregnancy", 4)
            return (
                target * ic.get("drugs_per_pregnant_woman", 0.3) * visits * years
                + target * ic.get("delivery_per_visit", 0.5) * visits * years
            )

        elif intervention == "vaccine":
            target = population * ic.get("target_proportion", 0.03)
            doses = ic.get("doses_per_child", 4)
            return (
                target * ic.get("vaccine_per_dose", 2.0) * doses * years
                + target * ic.get("delivery_per_dose", 1.5) * doses * years
            )

        elif intervention == "cm":
            tests = population * ic.get("test_rate", 0.15)
            treatments = tests * ic.get("positivity_rate", 0.3)
            return (
                tests * ic.get("rdt_per_test", 0.5) * years
                + treatments * ic.get("act_per_treatment", 1.2) * years
            )

        elif intervention == "pmc":
            target = population * ic.get("infant_proportion", 0.03)
            doses = ic.get("doses", 3)
            return (
                target * ic.get("drugs_per_infant_per_dose", 0.4) * doses * years
                + target * ic.get("delivery_per_dose", 0.5) * doses * years
            )

        elif intervention == "lsm":
            hectares = (population / 1000) * ic.get("hectares_per_1000_pop", 0.5)
            return hectares * ic.get("cost_per_hectare_per_year", 150) * years

        return 0.0

    def _estimate_effect(self, intervention: str, population: int) -> float:
        """Simplified effect estimate (cases averted) for optimization."""
        # These are rough multipliers for cost-effectiveness ranking
        effect_rates = {
            "itn": 0.05,      # 5% cases averted per capita covered
            "irs": 0.04,
            "smc": 0.06,
            "cm": 0.03,
            "iptp": 0.01,
            "vaccine": 0.02,
            "pmc": 0.015,
            "lsm": 0.005,
        }
        rate = effect_rates.get(intervention, 0.01)
        return population * rate

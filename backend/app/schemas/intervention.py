import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.enums import InterventionCode, RiskLevel, ScenarioType


# --- Decision Tree Schemas ---


class TailoringOption(BaseModel):
    value: str
    label: str
    conditions: dict[str, Any] | None = None
    help_text: str | None = None


class TailoringQuestion(BaseModel):
    id: str
    question: str
    question_type: str = "select"  # "select", "numeric", "boolean"
    options: list[TailoringOption] | None = None
    default: Any | None = None
    min_value: float | None = None
    max_value: float | None = None
    help_text: str | None = None


class InterventionDecisionTree(BaseModel):
    intervention_code: InterventionCode
    intervention_name: str
    eligibility_criteria: list[dict[str, Any]]
    tailoring_questions: list[TailoringQuestion]


class InterventionRecommendation(BaseModel):
    intervention_code: InterventionCode
    intervention_name: str
    is_eligible: bool
    ineligibility_reasons: list[str] | None = None
    tailoring_questions: list[TailoringQuestion] | None = None
    default_recommendations: dict[str, Any] | None = None
    context_summary: dict[str, Any] | None = None


# --- Intervention Plan Schemas ---


class InterventionPlanCreate(BaseModel):
    admin_unit_name: str = Field(min_length=1, max_length=255)
    admin_unit_code: str | None = None
    intervention_code: InterventionCode
    tailoring_decisions: dict[str, Any] | None = None
    coverage_target: float | None = Field(default=None, ge=0, le=100)
    delivery_strategy: str | None = None
    target_population: int | None = None
    notes: str | None = None


class InterventionPlanResponse(BaseModel):
    id: uuid.UUID
    admin_unit_name: str
    admin_unit_code: str | None
    intervention_code: InterventionCode
    is_eligible: bool
    tailoring_decisions: dict | None
    coverage_target: float | None
    delivery_strategy: str | None
    target_population: int | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Scenario Schemas ---


class ScenarioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    scenario_type: ScenarioType = ScenarioType.CUSTOM
    interventions: dict[str, list[str]]
    # {"district_code": ["itn", "smc"], ...}


class ScenarioUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    interventions: dict[str, list[str]] | None = None
    is_selected: bool | None = None


class ScenarioCostItemResponse(BaseModel):
    id: uuid.UUID
    admin_unit_name: str
    admin_unit_code: str | None
    intervention_code: str
    unit_cost: float | None
    quantity: int | None
    total_cost: float
    cost_category: str | None
    years: int

    model_config = {"from_attributes": True}


class ScenarioResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    scenario_type: ScenarioType
    is_selected: bool
    interventions: dict
    total_cost: float | None
    population_covered: int | None
    estimated_cases_averted: int | None
    estimated_deaths_averted: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScenarioDetailResponse(ScenarioResponse):
    cost_items: list[ScenarioCostItemResponse]


class ScenarioCostSummary(BaseModel):
    scenario_id: uuid.UUID
    scenario_name: str
    total_cost: float
    cost_by_intervention: dict[str, float]
    cost_by_unit: dict[str, float]
    cost_per_capita: float | None
    total_population: int


class ScenarioComparisonResponse(BaseModel):
    scenarios: list[ScenarioResponse]
    comparison_metrics: dict[str, dict[str, Any]]
    # {"scenario_id": {"total_cost": X, "cases_averted": Y, "icer": Z, ...}}

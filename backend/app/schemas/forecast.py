import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.enums import ForecastStatus


class ForecastRequest(BaseModel):
    model_type: str = "simple"  # "simple", "openmalaria", "emod"
    parameters: dict[str, Any] | None = None
    projection_years: int = Field(default=5, ge=1, le=20)


class ForecastResultResponse(BaseModel):
    id: uuid.UUID
    scenario_id: uuid.UUID
    status: ForecastStatus
    model_type: str | None
    projected_cases: dict | None
    projected_deaths: dict | None
    projected_prevalence: dict | None
    cases_averted: int | None
    deaths_averted: int | None
    dalys_averted: float | None
    cost_per_case_averted: float | None
    cost_per_death_averted: float | None
    cost_per_daly_averted: float | None
    uncertainty_bounds: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ForecastSummaryResponse(BaseModel):
    scenario_id: uuid.UUID
    scenario_name: str
    baseline_cases: int
    baseline_deaths: int
    projected_cases_final_year: int | None
    projected_deaths_final_year: int | None
    total_cases_averted: int | None
    total_deaths_averted: int | None
    cost_effectiveness: dict[str, float | None]


class ForecastComparisonResponse(BaseModel):
    scenarios: list[ForecastSummaryResponse]
    best_by_cases_averted: uuid.UUID | None
    best_by_cost_effectiveness: uuid.UUID | None

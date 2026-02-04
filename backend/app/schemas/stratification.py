import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.enums import RiskLevel, StratificationMetric


class ThresholdRange(BaseModel):
    min_value: float = Field(ge=0)
    max_value: float


class StratificationConfigCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    metric: StratificationMetric
    thresholds: dict[str, ThresholdRange]


class StratificationConfigUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    thresholds: dict[str, ThresholdRange] | None = None
    is_active: bool | None = None


class StratificationConfigResponse(BaseModel):
    id: uuid.UUID
    name: str
    metric: StratificationMetric
    thresholds: dict
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class StratificationResultResponse(BaseModel):
    id: uuid.UUID
    admin_unit_name: str
    admin_unit_code: str | None
    metric_value: float
    risk_level: RiskLevel
    eligible_interventions: dict | None
    population: int | None
    cases_annual: int | None
    deaths_annual: int | None

    model_config = {"from_attributes": True}


class StratificationSummaryResponse(BaseModel):
    config_id: uuid.UUID
    config_name: str
    metric: StratificationMetric
    total_units: int
    risk_distribution: dict[str, int]
    total_population: int
    total_cases: int


# GeoJSON schemas
class GeoJSONGeometry(BaseModel):
    type: str
    coordinates: Any


class GeoJSONProperties(BaseModel):
    unit_id: uuid.UUID
    unit_name: str
    unit_code: str | None
    risk_level: RiskLevel
    metric_value: float
    population: int | None
    cases_annual: int | None
    deaths_annual: int | None
    eligible_interventions: list[str] | None


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: GeoJSONGeometry | None
    properties: GeoJSONProperties


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[GeoJSONFeature]

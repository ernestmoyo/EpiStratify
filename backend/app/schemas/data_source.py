import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import DataSourceType, QualityCheckStatus, QualityCheckType


class DataSourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    source_type: DataSourceType
    year_start: int | None = Field(default=None, ge=1990, le=2100)
    year_end: int | None = Field(default=None, ge=1990, le=2100)
    disaggregation: dict | None = None


class QualityCheckResponse(BaseModel):
    id: uuid.UUID
    check_type: QualityCheckType
    status: QualityCheckStatus
    score: float | None
    issues_found: int
    message: str | None
    details: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DataSourceResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    source_type: DataSourceType
    file_format: str | None
    file_size_bytes: int | None
    record_count: int | None
    year_start: int | None
    year_end: int | None
    quality_score: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DataSourceDetailResponse(DataSourceResponse):
    quality_checks: list[QualityCheckResponse]
    temporal_coverage: dict | None
    spatial_coverage: dict | None
    disaggregation: dict | None


class QualityReportResponse(BaseModel):
    data_source_id: uuid.UUID
    data_source_name: str
    overall_score: float | None
    checks: list[QualityCheckResponse]
    recommendations: list[str]

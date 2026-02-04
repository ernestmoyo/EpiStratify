import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import ReportFormat


class ReportGenerateRequest(BaseModel):
    report_type: str = "full_snt"
    # "full_snt", "executive_summary", "stratification", "budget", "step_summary"
    format: ReportFormat = ReportFormat.PDF
    title: str | None = None
    parameters: dict | None = None
    # e.g. {"steps": [1,2,3], "include_maps": true}


class ReportRecordResponse(BaseModel):
    id: uuid.UUID
    title: str
    report_type: str
    format: str
    file_size_bytes: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    items: list[ReportRecordResponse]
    total: int

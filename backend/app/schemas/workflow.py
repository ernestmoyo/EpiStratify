import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import StepStatus, WorkflowStep


class StepStatusResponse(BaseModel):
    step: WorkflowStep
    label: str
    status: StepStatus
    completion_percentage: float
    is_accessible: bool
    blocking_prerequisites: list[str]
    non_blocking_prerequisites: list[str]
    notes: str | None
    completed_at: datetime | None
    data: dict | None = None
    validation_errors: dict | None = None


class WorkflowStateResponse(BaseModel):
    project_id: uuid.UUID
    steps: list[StepStatusResponse]
    overall_progress: float
    current_step: WorkflowStep | None


class StepUpdateRequest(BaseModel):
    notes: str | None = None
    completion_percentage: float | None = Field(default=None, ge=0, le=100)
    data: dict | None = None


class StepValidationResponse(BaseModel):
    step: WorkflowStep
    is_valid: bool
    errors: list[str]
    warnings: list[str]

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import ProjectRole, ProjectStatus


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    country: str = Field(min_length=1, max_length=100)
    admin_level: int = Field(default=1, ge=0, le=4)
    year: int = Field(ge=2000, le=2100)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    country: str | None = Field(default=None, min_length=1, max_length=100)
    admin_level: int | None = Field(default=None, ge=0, le=4)
    year: int | None = Field(default=None, ge=2000, le=2100)


class ProjectMemberResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    role: ProjectRole
    user_email: str | None = None
    user_name: str | None = None

    model_config = {"from_attributes": True}


class ProjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    country: str
    admin_level: int
    year: int
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int

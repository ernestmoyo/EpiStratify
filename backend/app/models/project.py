import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Project(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    admin_level: Mapped[int] = mapped_column(Integer, default=1)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)

    members: Mapped[list["ProjectMember"]] = relationship(
        "ProjectMember", back_populates="project", cascade="all, delete-orphan"
    )
    workflow_states: Mapped[list["WorkflowState"]] = relationship(
        "WorkflowState", back_populates="project", cascade="all, delete-orphan"
    )
    data_sources: Mapped[list["DataSource"]] = relationship(
        "DataSource", back_populates="project", cascade="all, delete-orphan"
    )
    stratification_configs: Mapped[list["StratificationConfig"]] = relationship(
        "StratificationConfig", back_populates="project", cascade="all, delete-orphan"
    )


class ProjectMember(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "project_members"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)

    project: Mapped["Project"] = relationship("Project", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="project_memberships")

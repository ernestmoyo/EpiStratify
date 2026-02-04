import uuid

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class StratificationConfig(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "stratification_configs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    metric: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    thresholds: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    project: Mapped["Project"] = relationship(
        "Project", back_populates="stratification_configs"
    )
    results: Mapped[list["StratificationResult"]] = relationship(
        "StratificationResult", back_populates="config", cascade="all, delete-orphan"
    )


class StratificationResult(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "stratification_results"

    config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stratification_configs.id"), nullable=False
    )
    admin_unit_name: Mapped[str] = mapped_column(String(255), nullable=False)
    admin_unit_code: Mapped[str | None] = mapped_column(String(50))
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    geometry = mapped_column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)
    eligible_interventions: Mapped[dict | None] = mapped_column(JSONB)
    population: Mapped[int | None] = mapped_column(Integer)
    cases_annual: Mapped[int | None] = mapped_column(Integer)
    deaths_annual: Mapped[int | None] = mapped_column(Integer)

    config: Mapped["StratificationConfig"] = relationship(
        "StratificationConfig", back_populates="results"
    )

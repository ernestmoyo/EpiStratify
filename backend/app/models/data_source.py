import uuid

from sqlalchemy import BigInteger, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class DataSource(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "data_sources"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(500))
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    file_format: Mapped[str | None] = mapped_column(String(20))
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    record_count: Mapped[int | None] = mapped_column(Integer)
    year_start: Mapped[int | None] = mapped_column(Integer)
    year_end: Mapped[int | None] = mapped_column(Integer)
    quality_score: Mapped[float | None] = mapped_column(Float)
    temporal_coverage: Mapped[dict | None] = mapped_column(JSONB)
    spatial_coverage: Mapped[dict | None] = mapped_column(JSONB)
    disaggregation: Mapped[dict | None] = mapped_column(JSONB)

    project: Mapped["Project"] = relationship("Project", back_populates="data_sources")
    quality_checks: Mapped[list["DataQualityCheck"]] = relationship(
        "DataQualityCheck", back_populates="data_source", cascade="all, delete-orphan"
    )


class DataQualityCheck(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "data_quality_checks"

    data_source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("data_sources.id"), nullable=False
    )
    check_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    score: Mapped[float | None] = mapped_column(Float)
    details: Mapped[dict | None] = mapped_column(JSONB)
    issues_found: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str | None] = mapped_column(Text)

    data_source: Mapped["DataSource"] = relationship(
        "DataSource", back_populates="quality_checks"
    )

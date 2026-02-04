import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class InterventionPlan(Base, UUIDMixin, TimestampMixin):
    """Stores intervention tailoring decisions for an operational unit."""

    __tablename__ = "intervention_plans"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    admin_unit_name: Mapped[str] = mapped_column(String(255), nullable=False)
    admin_unit_code: Mapped[str | None] = mapped_column(String(50))
    intervention_code: Mapped[str] = mapped_column(String(20), nullable=False)
    is_eligible: Mapped[bool] = mapped_column(Boolean, default=True)

    # Tailoring decisions (answers to decision tree questions)
    tailoring_decisions: Mapped[dict | None] = mapped_column(JSONB)
    # e.g. {"itn_type": "PBO_LLIN", "distribution_strategy": "MASS_CAMPAIGN", "coverage_target": 80}

    coverage_target: Mapped[float | None] = mapped_column(Float)  # 0-100%
    delivery_strategy: Mapped[str | None] = mapped_column(String(100))
    target_population: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )


class InterventionScenario(Base, UUIDMixin, TimestampMixin):
    """Stores intervention combination scenarios for a project."""

    __tablename__ = "intervention_scenarios"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    scenario_type: Mapped[str] = mapped_column(String(30), nullable=False)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)

    # Interventions by operational unit
    # {"unit_code": ["ITN", "SMC"], ...}
    interventions: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Aggregated metrics (populated after costing/forecasting)
    total_cost: Mapped[float | None] = mapped_column(Float)
    population_covered: Mapped[int | None] = mapped_column(Integer)
    estimated_cases_averted: Mapped[int | None] = mapped_column(Integer)
    estimated_deaths_averted: Mapped[int | None] = mapped_column(Integer)

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Relationships
    cost_items: Mapped[list["ScenarioCostItem"]] = relationship(
        "ScenarioCostItem", back_populates="scenario", cascade="all, delete-orphan"
    )
    forecasts: Mapped[list["ForecastResult"]] = relationship(
        "ForecastResult", back_populates="scenario", cascade="all, delete-orphan"
    )


class ScenarioCostItem(Base, UUIDMixin, TimestampMixin):
    """Individual cost line items for a scenario."""

    __tablename__ = "scenario_cost_items"

    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("intervention_scenarios.id"), nullable=False
    )
    admin_unit_name: Mapped[str] = mapped_column(String(255), nullable=False)
    admin_unit_code: Mapped[str | None] = mapped_column(String(50))
    intervention_code: Mapped[str] = mapped_column(String(20), nullable=False)

    # Cost breakdown
    unit_cost: Mapped[float | None] = mapped_column(Float)
    quantity: Mapped[int | None] = mapped_column(Integer)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
    cost_category: Mapped[str | None] = mapped_column(String(50))
    # e.g. "procurement", "distribution", "training", "supervision"

    cost_details: Mapped[dict | None] = mapped_column(JSONB)
    years: Mapped[int] = mapped_column(Integer, default=1)

    scenario: Mapped["InterventionScenario"] = relationship(
        "InterventionScenario", back_populates="cost_items"
    )


class ForecastResult(Base, UUIDMixin, TimestampMixin):
    """Stores impact forecasting results for a scenario."""

    __tablename__ = "forecast_results"

    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("intervention_scenarios.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="pending")
    model_type: Mapped[str | None] = mapped_column(String(50))

    # Projected outcomes by year
    projected_cases: Mapped[dict | None] = mapped_column(JSONB)
    # {"2025": 50000, "2026": 45000, ...}
    projected_deaths: Mapped[dict | None] = mapped_column(JSONB)
    projected_prevalence: Mapped[dict | None] = mapped_column(JSONB)

    # Impact metrics
    cases_averted: Mapped[int | None] = mapped_column(Integer)
    deaths_averted: Mapped[int | None] = mapped_column(Integer)
    dalys_averted: Mapped[float | None] = mapped_column(Float)

    # Cost-effectiveness
    cost_per_case_averted: Mapped[float | None] = mapped_column(Float)
    cost_per_death_averted: Mapped[float | None] = mapped_column(Float)
    cost_per_daly_averted: Mapped[float | None] = mapped_column(Float)

    # Uncertainty bounds
    uncertainty_bounds: Mapped[dict | None] = mapped_column(JSONB)
    # {"cases_averted": {"lower": 40000, "upper": 60000}, ...}

    parameters: Mapped[dict | None] = mapped_column(JSONB)

    scenario: Mapped["InterventionScenario"] = relationship(
        "InterventionScenario", back_populates="forecasts"
    )


class ReportRecord(Base, UUIDMixin, TimestampMixin):
    """Tracks generated reports."""

    __tablename__ = "report_records"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # e.g. "full_snt", "step_summary", "stratification", "budget", "executive"
    format: Mapped[str] = mapped_column(String(10), default="pdf")
    file_path: Mapped[str | None] = mapped_column(String(500))
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    parameters: Mapped[dict | None] = mapped_column(JSONB)
    generated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

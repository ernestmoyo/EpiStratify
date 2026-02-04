"""Automated report generation for SNT projects."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.enums import ForecastStatus, ReportFormat, WorkflowStep
from app.models.data_source import DataQualityCheck, DataSource
from app.models.intervention import (
    ForecastResult,
    InterventionScenario,
    ReportRecord,
    ScenarioCostItem,
)
from app.models.project import Project
from app.models.stratification import StratificationConfig, StratificationResult
from app.models.user import User
from app.models.workflow import WorkflowState
from app.schemas.report import ReportGenerateRequest, ReportListResponse, ReportRecordResponse


class ReportService:
    """Generates structured reports for SNT projects."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_report(
        self,
        project_id: uuid.UUID,
        request: ReportGenerateRequest,
        user: User,
    ) -> ReportRecordResponse:
        """Generate a report and save as a file."""
        # Fetch project
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if project is None:
            raise ValueError("Project not found")

        title = request.title or f"{project.name} - {self._report_type_label(request.report_type)}"

        # Gather report data
        report_data = await self._gather_report_data(
            project_id, request.report_type, request.parameters
        )

        # Generate file content
        file_content, file_ext = self._render_report(
            report_data, request.format, title
        )

        # Save file
        reports_dir = Path(settings.UPLOAD_DIR) / str(project_id) / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{request.report_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}{file_ext}"
        file_path = reports_dir / filename

        with open(file_path, "wb") as f:
            f.write(file_content)

        relative_path = str(file_path.relative_to(Path(settings.UPLOAD_DIR)))

        # Create record
        record = ReportRecord(
            project_id=project_id,
            title=title,
            report_type=request.report_type,
            format=request.format.value,
            file_path=relative_path,
            file_size_bytes=len(file_content),
            parameters=request.parameters,
            generated_by=user.id,
        )
        self.db.add(record)
        await self.db.flush()

        return ReportRecordResponse.model_validate(record)

    async def list_reports(
        self, project_id: uuid.UUID
    ) -> ReportListResponse:
        result = await self.db.execute(
            select(ReportRecord)
            .where(ReportRecord.project_id == project_id)
            .order_by(ReportRecord.created_at.desc())
        )
        reports = result.scalars().all()
        return ReportListResponse(
            items=[ReportRecordResponse.model_validate(r) for r in reports],
            total=len(reports),
        )

    async def get_report(
        self, report_id: uuid.UUID
    ) -> ReportRecordResponse:
        result = await self.db.execute(
            select(ReportRecord).where(ReportRecord.id == report_id)
        )
        record = result.scalar_one_or_none()
        if record is None:
            raise ValueError("Report not found")
        return ReportRecordResponse.model_validate(record)

    async def get_report_file_path(self, report_id: uuid.UUID) -> Path:
        result = await self.db.execute(
            select(ReportRecord).where(ReportRecord.id == report_id)
        )
        record = result.scalar_one_or_none()
        if record is None:
            raise ValueError("Report not found")
        if record.file_path is None:
            raise ValueError("Report file not available")
        return Path(settings.UPLOAD_DIR) / record.file_path

    async def delete_report(self, report_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(ReportRecord).where(ReportRecord.id == report_id)
        )
        record = result.scalar_one_or_none()
        if record is None:
            raise ValueError("Report not found")

        # Delete file
        if record.file_path:
            file_path = Path(settings.UPLOAD_DIR) / record.file_path
            if file_path.exists():
                file_path.unlink()

        await self.db.delete(record)

    # --- Data gathering ---

    async def _gather_report_data(
        self,
        project_id: uuid.UUID,
        report_type: str,
        parameters: dict | None = None,
    ) -> dict[str, Any]:
        """Gather all data needed for the report."""
        data: dict[str, Any] = {
            "generated_at": datetime.utcnow().isoformat(),
            "report_type": report_type,
        }

        # Project info
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if project:
            data["project"] = {
                "name": project.name,
                "country": project.country,
                "year": project.year,
                "description": project.description,
            }

        # Workflow status
        wf_result = await self.db.execute(
            select(WorkflowState).where(WorkflowState.project_id == project_id)
        )
        states = wf_result.scalars().all()
        data["workflow"] = [
            {
                "step": s.step,
                "status": s.status,
                "completion_percentage": s.completion_percentage,
            }
            for s in states
        ]

        if report_type in ("full_snt", "stratification"):
            data["stratification"] = await self._gather_stratification(project_id)

        if report_type in ("full_snt", "budget"):
            data["scenarios"] = await self._gather_scenarios(project_id)

        if report_type in ("full_snt", "executive_summary"):
            data["data_quality"] = await self._gather_data_quality(project_id)
            data["stratification"] = await self._gather_stratification(project_id)
            data["scenarios"] = await self._gather_scenarios(project_id)
            data["forecasts"] = await self._gather_forecasts(project_id)

        return data

    async def _gather_stratification(self, project_id: uuid.UUID) -> dict:
        configs_result = await self.db.execute(
            select(StratificationConfig).where(
                StratificationConfig.project_id == project_id
            )
        )
        configs = configs_result.scalars().all()

        strat_data: dict[str, Any] = {"configs": []}
        for config in configs:
            results_result = await self.db.execute(
                select(StratificationResult).where(
                    StratificationResult.config_id == config.id
                )
            )
            results = results_result.scalars().all()

            risk_distribution: dict[str, int] = {}
            for r in results:
                level = r.risk_level or "unknown"
                risk_distribution[level] = risk_distribution.get(level, 0) + 1

            strat_data["configs"].append({
                "metric": config.metric,
                "total_units": len(results),
                "risk_distribution": risk_distribution,
            })

        return strat_data

    async def _gather_scenarios(self, project_id: uuid.UUID) -> list[dict]:
        result = await self.db.execute(
            select(InterventionScenario).where(
                InterventionScenario.project_id == project_id
            )
        )
        scenarios = result.scalars().all()

        scenario_list = []
        for s in scenarios:
            cost_result = await self.db.execute(
                select(func.sum(ScenarioCostItem.total_cost)).where(
                    ScenarioCostItem.scenario_id == s.id
                )
            )
            cost_total = cost_result.scalar() or 0

            scenario_list.append({
                "name": s.name,
                "type": s.scenario_type,
                "is_selected": s.is_selected,
                "interventions": s.interventions,
                "total_cost": s.total_cost or cost_total,
                "population_covered": s.population_covered,
                "estimated_cases_averted": s.estimated_cases_averted,
                "estimated_deaths_averted": s.estimated_deaths_averted,
            })

        return scenario_list

    async def _gather_data_quality(self, project_id: uuid.UUID) -> dict:
        ds_result = await self.db.execute(
            select(DataSource).where(DataSource.project_id == project_id)
        )
        sources = ds_result.scalars().all()

        return {
            "total_sources": len(sources),
            "sources": [
                {
                    "name": s.name,
                    "type": s.source_type,
                    "quality_score": s.quality_score,
                }
                for s in sources
            ],
        }

    async def _gather_forecasts(self, project_id: uuid.UUID) -> list[dict]:
        result = await self.db.execute(
            select(InterventionScenario).where(
                InterventionScenario.project_id == project_id
            )
        )
        scenarios = result.scalars().all()

        forecasts = []
        for s in scenarios:
            fr = await self.db.execute(
                select(ForecastResult)
                .where(
                    ForecastResult.scenario_id == s.id,
                    ForecastResult.status == ForecastStatus.COMPLETED.value,
                )
                .order_by(ForecastResult.created_at.desc())
                .limit(1)
            )
            forecast = fr.scalar_one_or_none()
            if forecast:
                forecasts.append({
                    "scenario_name": s.name,
                    "cases_averted": forecast.cases_averted,
                    "deaths_averted": forecast.deaths_averted,
                    "dalys_averted": forecast.dalys_averted,
                    "cost_per_case_averted": forecast.cost_per_case_averted,
                    "cost_per_daly_averted": forecast.cost_per_daly_averted,
                })

        return forecasts

    # --- Rendering ---

    def _render_report(
        self,
        data: dict,
        fmt: ReportFormat,
        title: str,
    ) -> tuple[bytes, str]:
        """Render report data to the requested format."""
        if fmt == ReportFormat.CSV:
            return self._render_csv(data, title), ".csv"
        elif fmt == ReportFormat.EXCEL:
            return self._render_json_as_excel_placeholder(data, title), ".json"
        else:
            # Default: structured JSON (PDF rendering requires wkhtmltopdf/WeasyPrint)
            return self._render_json(data, title), ".json"

    def _render_json(self, data: dict, title: str) -> bytes:
        """Render as structured JSON report."""
        report = {"title": title, **data}
        return json.dumps(report, indent=2, default=str).encode("utf-8")

    def _render_csv(self, data: dict, title: str) -> bytes:
        """Render key metrics as CSV."""
        lines = [f"# {title}", ""]

        # Workflow status
        lines.append("Step,Status,Completion %")
        for step in data.get("workflow", []):
            lines.append(
                f"{step['step']},{step['status']},{step.get('completion_percentage', 0)}"
            )

        # Scenarios
        scenarios = data.get("scenarios", [])
        if scenarios:
            lines.append("")
            lines.append("Scenario,Type,Total Cost,Cases Averted,Deaths Averted")
            for s in scenarios:
                lines.append(
                    f"{s['name']},{s['type']},{s.get('total_cost', 0)},"
                    f"{s.get('estimated_cases_averted', '')},{s.get('estimated_deaths_averted', '')}"
                )

        # Forecasts
        forecasts = data.get("forecasts", [])
        if forecasts:
            lines.append("")
            lines.append("Scenario,Cases Averted,Deaths Averted,DALYs Averted,Cost/Case,Cost/DALY")
            for f in forecasts:
                lines.append(
                    f"{f['scenario_name']},{f.get('cases_averted', '')},"
                    f"{f.get('deaths_averted', '')},{f.get('dalys_averted', '')},"
                    f"{f.get('cost_per_case_averted', '')},{f.get('cost_per_daly_averted', '')}"
                )

        return "\n".join(lines).encode("utf-8")

    def _render_json_as_excel_placeholder(self, data: dict, title: str) -> bytes:
        """Placeholder: renders JSON. Real Excel generation needs openpyxl."""
        return self._render_json(data, title)

    def _report_type_label(self, report_type: str) -> str:
        labels = {
            "full_snt": "Full SNT Report",
            "executive_summary": "Executive Summary",
            "stratification": "Stratification Report",
            "budget": "Budget Report",
            "step_summary": "Step Summary",
        }
        return labels.get(report_type, report_type.replace("_", " ").title())

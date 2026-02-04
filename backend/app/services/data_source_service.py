import uuid
from pathlib import Path

import pandas as pd
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import DataSourceType
from app.models.data_source import DataQualityCheck, DataSource
from app.models.user import User
from app.schemas.data_source import (
    DataSourceCreate,
    DataSourceDetailResponse,
    DataSourceResponse,
    QualityCheckResponse,
    QualityReportResponse,
)
from app.services.file_storage_service import FileStorageService
from app.services.quality_check_service import QualityCheckService


class DataSourceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.file_storage = FileStorageService()
        self.quality_checker = QualityCheckService(db)

    async def upload_data_source(
        self,
        project_id: uuid.UUID,
        metadata: DataSourceCreate,
        file: UploadFile,
        user: User,
    ) -> DataSourceResponse:
        """Upload a data source file and create metadata record."""
        content = await file.read()
        file_size = len(content)

        # Determine format
        file_ext = Path(file.filename).suffix.lower() if file.filename else ""
        format_map = {
            ".csv": "csv",
            ".xlsx": "xlsx",
            ".xls": "xls",
            ".geojson": "geojson",
            ".json": "json",
            ".shp": "shp",
        }
        file_format = format_map.get(file_ext, "unknown")

        # Save file
        relative_path = await self.file_storage.save_file(
            content, project_id, file.filename or "upload"
        )

        # Count records if possible
        record_count = await self._count_records(content, file_format)

        data_source = DataSource(
            project_id=project_id,
            name=metadata.name,
            description=metadata.description,
            source_type=metadata.source_type.value,
            file_path=relative_path,
            file_size_bytes=file_size,
            file_format=file_format,
            uploaded_by=user.id,
            record_count=record_count,
            year_start=metadata.year_start,
            year_end=metadata.year_end,
            disaggregation=metadata.disaggregation,
        )
        self.db.add(data_source)
        await self.db.flush()

        return DataSourceResponse.model_validate(data_source)

    async def list_data_sources(
        self, project_id: uuid.UUID
    ) -> list[DataSourceResponse]:
        result = await self.db.execute(
            select(DataSource)
            .where(DataSource.project_id == project_id)
            .order_by(DataSource.created_at.desc())
        )
        sources = result.scalars().all()
        return [DataSourceResponse.model_validate(s) for s in sources]

    async def get_data_source(
        self, data_source_id: uuid.UUID
    ) -> DataSourceDetailResponse:
        result = await self.db.execute(
            select(DataSource).where(DataSource.id == data_source_id)
        )
        ds = result.scalar_one_or_none()
        if ds is None:
            raise ValueError("Data source not found")

        # Fetch quality checks
        checks_result = await self.db.execute(
            select(DataQualityCheck)
            .where(DataQualityCheck.data_source_id == data_source_id)
            .order_by(DataQualityCheck.created_at.desc())
        )
        checks = checks_result.scalars().all()

        return DataSourceDetailResponse(
            id=ds.id,
            name=ds.name,
            description=ds.description,
            source_type=DataSourceType(ds.source_type),
            file_format=ds.file_format,
            file_size_bytes=ds.file_size_bytes,
            record_count=ds.record_count,
            year_start=ds.year_start,
            year_end=ds.year_end,
            quality_score=ds.quality_score,
            created_at=ds.created_at,
            quality_checks=[QualityCheckResponse.model_validate(c) for c in checks],
            temporal_coverage=ds.temporal_coverage,
            spatial_coverage=ds.spatial_coverage,
            disaggregation=ds.disaggregation,
        )

    async def delete_data_source(self, data_source_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(DataSource).where(DataSource.id == data_source_id)
        )
        ds = result.scalar_one_or_none()
        if ds is None:
            raise ValueError("Data source not found")

        if ds.file_path:
            await self.file_storage.delete_file(ds.file_path)

        await self.db.delete(ds)

    async def run_quality_checks(
        self, data_source_id: uuid.UUID
    ) -> QualityReportResponse:
        """Run all quality checks on a data source."""
        result = await self.db.execute(
            select(DataSource).where(DataSource.id == data_source_id)
        )
        ds = result.scalar_one_or_none()
        if ds is None:
            raise ValueError("Data source not found")

        report = await self.quality_checker.run_all_checks(ds)

        # Update overall quality score on data source
        ds.quality_score = report.overall_score
        await self.db.flush()

        return report

    async def get_quality_report(
        self, data_source_id: uuid.UUID
    ) -> QualityReportResponse:
        """Get existing quality report for a data source."""
        result = await self.db.execute(
            select(DataSource).where(DataSource.id == data_source_id)
        )
        ds = result.scalar_one_or_none()
        if ds is None:
            raise ValueError("Data source not found")

        checks_result = await self.db.execute(
            select(DataQualityCheck)
            .where(DataQualityCheck.data_source_id == data_source_id)
            .order_by(DataQualityCheck.created_at.desc())
        )
        checks = checks_result.scalars().all()

        recommendations = self._generate_recommendations(checks)

        return QualityReportResponse(
            data_source_id=ds.id,
            data_source_name=ds.name,
            overall_score=ds.quality_score,
            checks=[QualityCheckResponse.model_validate(c) for c in checks],
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self, checks: list[DataQualityCheck]
    ) -> list[str]:
        recommendations = []
        for check in checks:
            if check.score is not None and check.score < 0.7:
                recommendations.append(
                    f"Improve {check.check_type}: score is {check.score:.0%}"
                )
            if check.issues_found > 0:
                recommendations.append(
                    f"Review {check.issues_found} issues in {check.check_type} check"
                )
        return recommendations

    async def _count_records(
        self, content: bytes, file_format: str
    ) -> int | None:
        try:
            if file_format == "csv":
                from io import BytesIO
                df = pd.read_csv(BytesIO(content))
                return len(df)
            elif file_format in ("xlsx", "xls"):
                from io import BytesIO
                df = pd.read_excel(BytesIO(content))
                return len(df)
        except Exception:
            pass
        return None

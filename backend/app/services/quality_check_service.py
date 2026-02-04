import io
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.enums import (
    DataSourceType,
    QualityCheckStatus,
    QualityCheckType,
)
from app.models.data_source import DataQualityCheck, DataSource
from app.schemas.data_source import QualityCheckResponse, QualityReportResponse


class QualityCheckService:
    """Automated data quality assessment based on WHO standards."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_all_checks(self, data_source: DataSource) -> QualityReportResponse:
        """Run all quality checks and return a report."""
        # Delete existing checks for this data source
        await self.db.execute(
            delete(DataQualityCheck).where(
                DataQualityCheck.data_source_id == data_source.id
            )
        )
        await self.db.flush()

        # Load data
        df = await self._load_data(data_source)
        if df is None:
            return QualityReportResponse(
                data_source_id=data_source.id,
                data_source_name=data_source.name,
                overall_score=None,
                checks=[],
                recommendations=["Could not load data file for quality checks"],
            )

        checks_to_run = [
            (QualityCheckType.COMPLETENESS, self._check_completeness),
            (QualityCheckType.CONSISTENCY, self._check_consistency),
            (QualityCheckType.OUTLIERS, self._check_outliers),
            (QualityCheckType.DISAGGREGATION, self._check_disaggregation),
            (QualityCheckType.DUPLICATES, self._check_duplicates),
        ]

        check_records = []
        scores = []

        for check_type, check_fn in checks_to_run:
            score, issues_found, message, details = check_fn(
                df, data_source
            )

            if score < 0.5:
                status = QualityCheckStatus.FAILED
            elif score < 0.8:
                status = QualityCheckStatus.WARNING
            else:
                status = QualityCheckStatus.PASSED

            record = DataQualityCheck(
                data_source_id=data_source.id,
                check_type=check_type.value,
                status=status.value,
                score=score,
                issues_found=issues_found,
                message=message,
                details=details,
            )
            self.db.add(record)
            check_records.append(record)
            scores.append(score)

        await self.db.flush()

        overall_score = sum(scores) / len(scores) if scores else 0.0

        recommendations = []
        for rec in check_records:
            if rec.score is not None and rec.score < 0.7:
                recommendations.append(
                    f"Improve {rec.check_type}: score is {rec.score:.0%}"
                )

        return QualityReportResponse(
            data_source_id=data_source.id,
            data_source_name=data_source.name,
            overall_score=overall_score,
            checks=[QualityCheckResponse.model_validate(r) for r in check_records],
            recommendations=recommendations,
        )

    def _check_completeness(
        self, df: pd.DataFrame, data_source: DataSource
    ) -> tuple[float, int, str, dict]:
        """Check for missing values and completeness."""
        total_cells = df.size
        missing_cells = int(df.isnull().sum().sum())
        missing_pct = (missing_cells / total_cells * 100) if total_cells > 0 else 0

        issues = []
        column_missing = {}
        for col in df.columns:
            col_missing = int(df[col].isnull().sum())
            if col_missing > 0:
                col_pct = col_missing / len(df) * 100
                column_missing[col] = {
                    "missing_count": col_missing,
                    "missing_pct": round(col_pct, 1),
                }
                if col_pct > 10:
                    issues.append(f"{col}: {col_pct:.1f}% missing")

        score = max(0.0, 1.0 - (missing_pct / 100))
        message = f"{missing_pct:.1f}% of data cells are missing"

        return (
            round(score, 3),
            len(issues),
            message,
            {"overall_missing_pct": round(missing_pct, 1), "columns": column_missing},
        )

    def _check_consistency(
        self, df: pd.DataFrame, data_source: DataSource
    ) -> tuple[float, int, str, dict]:
        """Check logical consistency of data."""
        issues = []
        details = {}

        # Check deaths <= cases
        if "cases" in df.columns and "deaths" in df.columns:
            inconsistent = df["deaths"] > df["cases"]
            count = int(inconsistent.sum())
            if count > 0:
                issues.append(f"Deaths > cases in {count} rows")
                details["deaths_gt_cases"] = count

        # Check confirmed + presumed <= total
        if all(
            c in df.columns
            for c in ["total_cases", "confirmed_cases", "presumed_cases"]
        ):
            inconsistent = df["total_cases"] < (
                df["confirmed_cases"] + df["presumed_cases"]
            )
            count = int(inconsistent.sum())
            if count > 0:
                issues.append(f"Total < confirmed + presumed in {count} rows")
                details["total_lt_sum"] = count

        # Check coverage 0-100%
        coverage_cols = [c for c in df.columns if "coverage" in c.lower()]
        for col in coverage_cols:
            if df[col].dtype in [np.float64, np.int64, float, int]:
                invalid = (df[col] < 0) | (df[col] > 100)
                count = int(invalid.sum())
                if count > 0:
                    issues.append(f"{col}: {count} values outside 0-100%")
                    details[f"invalid_{col}"] = count

        # Check negative values in count columns
        count_cols = [
            c
            for c in df.columns
            if any(
                kw in c.lower()
                for kw in ["cases", "deaths", "population", "tests"]
            )
        ]
        for col in count_cols:
            if df[col].dtype in [np.float64, np.int64, float, int]:
                negative = df[col] < 0
                count = int(negative.sum())
                if count > 0:
                    issues.append(f"{col}: {count} negative values")
                    details[f"negative_{col}"] = count

        score = max(0.0, 1.0 - (len(issues) * 0.15))
        message = (
            f"{len(issues)} consistency issues found"
            if issues
            else "No consistency issues found"
        )

        return round(score, 3), len(issues), message, details

    def _check_outliers(
        self, df: pd.DataFrame, data_source: DataSource
    ) -> tuple[float, int, str, dict]:
        """Detect statistical outliers using IQR method."""
        issues = []
        details = {}
        exclude_cols = {"id", "year", "month", "day", "date", "code"}

        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col.lower() in exclude_cols:
                continue

            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1

            if iqr == 0:
                continue

            outlier_mask = (df[col] < (q1 - 3 * iqr)) | (df[col] > (q3 + 3 * iqr))
            outlier_count = int(outlier_mask.sum())

            if outlier_count > 0:
                outlier_pct = outlier_count / len(df) * 100
                if outlier_pct > 5:
                    issues.append(
                        f"{col}: {outlier_count} outliers ({outlier_pct:.1f}%)"
                    )
                details[col] = {
                    "outlier_count": outlier_count,
                    "outlier_pct": round(outlier_pct, 1),
                    "q1": round(float(q1), 2),
                    "q3": round(float(q3), 2),
                    "iqr": round(float(iqr), 2),
                }

        score = max(0.0, 1.0 - (len(issues) * 0.1))
        message = (
            f"{len(issues)} columns with significant outliers"
            if issues
            else "No significant outliers detected"
        )

        return round(score, 3), len(issues), message, details

    def _check_disaggregation(
        self, df: pd.DataFrame, data_source: DataSource
    ) -> tuple[float, int, str, dict]:
        """Check data disaggregation by age, sex, geography."""
        issues = []
        details = {"has_age": False, "has_sex": False, "has_geography": False}
        expected = data_source.disaggregation or {}

        # Check age disaggregation
        age_cols = [c for c in df.columns if "age" in c.lower()]
        if age_cols:
            details["has_age"] = True
        elif expected.get("age"):
            issues.append("Expected age disaggregation not found")

        # Check sex disaggregation
        sex_cols = [c for c in df.columns if c.lower() in ("sex", "gender")]
        if sex_cols:
            details["has_sex"] = True
            # Validate values
            for col in sex_cols:
                valid_values = {"Male", "Female", "M", "F", "male", "female"}
                invalid = ~df[col].dropna().isin(valid_values)
                count = int(invalid.sum())
                if count > 0:
                    issues.append(f"Invalid {col} values in {count} rows")
                    details["invalid_sex_values"] = count
        elif expected.get("sex"):
            issues.append("Expected sex disaggregation not found")

        # Check geographic disaggregation
        geo_cols = [
            c
            for c in df.columns
            if c.lower() in ("district", "region", "province", "admin1", "admin2")
        ]
        if geo_cols:
            details["has_geography"] = True
        elif expected.get("geography"):
            issues.append("Expected geographic disaggregation not found")

        score = max(0.0, 1.0 - (len(issues) * 0.2))
        message = (
            f"{len(issues)} disaggregation issues found"
            if issues
            else "Disaggregation checks passed"
        )

        return round(score, 3), len(issues), message, details

    def _check_duplicates(
        self, df: pd.DataFrame, data_source: DataSource
    ) -> tuple[float, int, str, dict]:
        """Check for duplicate rows."""
        dup_count = int(df.duplicated().sum())
        total_rows = len(df)
        dup_pct = (dup_count / total_rows * 100) if total_rows > 0 else 0

        score = max(0.0, 1.0 - (dup_pct / 50))  # 50% duplicates = 0 score
        message = f"{dup_count} duplicate rows found ({dup_pct:.1f}%)"

        return (
            round(score, 3),
            1 if dup_count > 0 else 0,
            message,
            {"duplicate_count": dup_count, "duplicate_pct": round(dup_pct, 1)},
        )

    async def _load_data(self, data_source: DataSource) -> pd.DataFrame | None:
        """Load data from file into a DataFrame."""
        if not data_source.file_path:
            return None

        file_path = Path(settings.UPLOAD_DIR) / data_source.file_path

        if not file_path.exists():
            return None

        try:
            if data_source.file_format == "csv":
                return pd.read_csv(file_path)
            elif data_source.file_format in ("xlsx", "xls"):
                return pd.read_excel(file_path)
            elif data_source.file_format == "geojson":
                import json

                with open(file_path) as f:
                    geojson = json.load(f)
                if "features" in geojson:
                    return pd.json_normalize(
                        geojson["features"],
                        sep="_",
                    )
            elif data_source.file_format == "json":
                return pd.read_json(file_path)
        except Exception:
            return None

        return None

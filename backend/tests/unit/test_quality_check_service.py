"""Unit tests for quality check logic."""

import numpy as np
import pandas as pd
import pytest

from app.services.quality_check_service import QualityCheckService


class TestCompletenessCheck:
    """Test completeness checking logic."""

    def setup_method(self):
        # Create service without DB (we'll test the check methods directly)
        self.service = QualityCheckService.__new__(QualityCheckService)

    def _make_data_source(self, **kwargs):
        """Create a mock data source."""

        class MockDS:
            pass

        ds = MockDS()
        ds.disaggregation = kwargs.get("disaggregation", {})
        return ds

    def test_complete_data_scores_high(self):
        df = pd.DataFrame(
            {
                "district": ["A", "B", "C"],
                "cases": [100, 200, 150],
                "deaths": [5, 10, 8],
            }
        )
        ds = self._make_data_source()
        score, issues, message, details = self.service._check_completeness(df, ds)
        assert score == 1.0
        assert issues == 0

    def test_missing_values_reduce_score(self):
        df = pd.DataFrame(
            {
                "district": ["A", "B", None, "D", None],
                "cases": [100, None, 150, None, None],
            }
        )
        ds = self._make_data_source()
        score, issues, message, details = self.service._check_completeness(df, ds)
        assert score < 1.0
        assert details["overall_missing_pct"] > 0

    def test_fully_null_column(self):
        df = pd.DataFrame(
            {
                "district": ["A", "B", "C"],
                "cases": [None, None, None],
            }
        )
        ds = self._make_data_source()
        score, issues, message, details = self.service._check_completeness(df, ds)
        assert score < 1.0


class TestConsistencyCheck:
    def setup_method(self):
        self.service = QualityCheckService.__new__(QualityCheckService)

    def _make_data_source(self, **kwargs):
        class MockDS:
            pass

        ds = MockDS()
        ds.disaggregation = kwargs.get("disaggregation", {})
        return ds

    def test_deaths_greater_than_cases_detected(self):
        df = pd.DataFrame(
            {
                "cases": [100, 50, 200],
                "deaths": [5, 100, 10],  # Row 1: deaths > cases
            }
        )
        ds = self._make_data_source()
        score, issues, message, details = self.service._check_consistency(df, ds)
        assert issues > 0
        assert "deaths_gt_cases" in details

    def test_consistent_data_passes(self):
        df = pd.DataFrame(
            {
                "cases": [100, 200, 300],
                "deaths": [5, 10, 15],
            }
        )
        ds = self._make_data_source()
        score, issues, message, details = self.service._check_consistency(df, ds)
        assert score == 1.0


class TestOutlierCheck:
    def setup_method(self):
        self.service = QualityCheckService.__new__(QualityCheckService)

    def _make_data_source(self, **kwargs):
        class MockDS:
            pass

        ds = MockDS()
        ds.disaggregation = kwargs.get("disaggregation", {})
        return ds

    def test_normal_data_no_outliers(self):
        np.random.seed(42)
        df = pd.DataFrame({"values": np.random.normal(100, 10, 100)})
        ds = self._make_data_source()
        score, issues, message, details = self.service._check_outliers(df, ds)
        assert score >= 0.8

    def test_extreme_outliers_detected(self):
        data = [100] * 95 + [100000] * 5  # 5% extreme outliers
        df = pd.DataFrame({"values": data})
        ds = self._make_data_source()
        score, issues, message, details = self.service._check_outliers(df, ds)
        assert "values" in details


class TestDisaggregationCheck:
    def setup_method(self):
        self.service = QualityCheckService.__new__(QualityCheckService)

    def _make_data_source(self, **kwargs):
        class MockDS:
            pass

        ds = MockDS()
        ds.disaggregation = kwargs.get("disaggregation", {})
        return ds

    def test_expected_disaggregation_present(self):
        df = pd.DataFrame(
            {
                "age_group": ["0-5", "5-15", "15+"],
                "sex": ["Male", "Female", "Male"],
                "district": ["A", "B", "C"],
            }
        )
        ds = self._make_data_source(
            disaggregation={"age": True, "sex": True, "geography": True}
        )
        score, issues, message, details = self.service._check_disaggregation(
            df, ds
        )
        assert score == 1.0
        assert details["has_age"]
        assert details["has_sex"]
        assert details["has_geography"]

    def test_missing_expected_disaggregation(self):
        df = pd.DataFrame({"cases": [100, 200, 300]})
        ds = self._make_data_source(
            disaggregation={"age": True, "sex": True, "geography": True}
        )
        score, issues, message, details = self.service._check_disaggregation(
            df, ds
        )
        assert score < 1.0
        assert issues >= 3

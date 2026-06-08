import pandas as pd
import pytest
from unittest.mock import patch, mock_open, MagicMock
from report_data import load_data, compute_ovd_stats


class TestLoadData:
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake_excel_data")
    @patch("report_data.load_data_from_bytes")
    def test_loads_excel(self, mock_load, mock_file):
        mock_load.return_value = (MagicMock(), MagicMock(), MagicMock())
        result = load_data()
        assert result is not None
        mock_load.assert_called_once()

    @patch("builtins.open", new_callable=mock_open, read_data=b"fake_data")
    @patch("report_data.load_data_from_bytes")
    def test_loads_from_excel_path(self, mock_load, mock_file):
        mock_load.return_value = (MagicMock(), MagicMock(), MagicMock())
        result = load_data()
        assert result is not None
        mock_load.assert_called_once_with(b"fake_data", b"fake_data")

    @patch("builtins.open")
    @patch("report_data.load_data_from_bytes")
    def test_csv_read_failure_does_not_crash(self, mock_load, mock_open):
        mock_open.side_effect = [MagicMock(), Exception("CSV not found")]
        mock_load.return_value = (MagicMock(), MagicMock(), MagicMock())
        result = load_data()
        assert result is not None


class TestComputeOvdStats:
    def _make_d(self, df_l=None):
        if df_l is None:
            dates = pd.to_datetime(["2026-04-01", "2025-10-01", "2025-04-01"])
            df_l = pd.DataFrame({
                "年月": dates,
                "逾放比": [0.035, 0.030, 0.025],
                "提撥率": [0.015, 0.016, 0.017],
            })
        return {"df_l": df_l}

    def test_basic_stats(self):
        d = self._make_d()
        stats = compute_ovd_stats(d)
        assert stats["curr"] == 0.025
        assert stats["months_total"] == 3

    def test_trend_improving(self):
        dates = pd.to_datetime(["2025-04-01", "2025-10-01", "2026-04-01"])
        df_l = pd.DataFrame({
            "年月": dates,
            "逾放比": [0.035, 0.030, 0.025],
            "提撥率": [0.015, 0.016, 0.017],
        })
        d = {"df_l": df_l}
        stats = compute_ovd_stats(d)
        assert stats["trend"] == "持續改善"
        assert stats["trend_color"] == "#10B981"

    def test_trend_worsening(self):
        dates = pd.to_datetime(["2026-04-01", "2025-10-01", "2025-04-01"])
        df_l = pd.DataFrame({
            "年月": dates,
            "逾放比": [0.025, 0.030, 0.035],
            "提撥率": [0.015, 0.016, 0.017],
        })
        d = self._make_d(df_l)
        stats = compute_ovd_stats(d)
        assert stats["trend"] == "持續惡化"
        assert stats["trend_color"] == "#EF4444"

    def test_trend_stable(self):
        dates = pd.to_datetime(["2026-04-01", "2025-10-01", "2025-04-01"])
        df_l = pd.DataFrame({
            "年月": dates,
            "逾放比": [0.030, 0.030, 0.030],
            "提撥率": [0.015, 0.016, 0.017],
        })
        d = self._make_d(df_l)
        stats = compute_ovd_stats(d)
        assert stats["trend"] == "趨於穩定"
        assert stats["trend_color"] == "#64748B"

    def test_empty_df_l(self):
        df_l = pd.DataFrame({"年月": pd.Series(dtype="datetime64[ns]"),
                              "逾放比": pd.Series(dtype="float64"),
                              "提撥率": pd.Series(dtype="float64")})
        d = {"df_l": df_l}
        stats = compute_ovd_stats(d)
        assert stats["months_total"] == 0
        assert stats["trend"] == "無資料"

    def test_missing_columns(self):
        df_l = pd.DataFrame({"年月": pd.to_datetime(["2026-04-01"])})
        d = {"df_l": df_l}
        stats = compute_ovd_stats(d)
        assert stats["trend"] == "無資料"

    def test_single_row(self):
        dates = pd.to_datetime(["2026-04-01"])
        df_l = pd.DataFrame({
            "年月": dates,
            "逾放比": [0.03],
            "提撥率": [0.015],
        })
        d = {"df_l": df_l}
        stats = compute_ovd_stats(d)
        assert stats["months_total"] == 1
        assert stats["trend"] == "趨於穩定"

    def test_warn_months_count(self):
        dates = pd.to_datetime(["2026-04-01", "2025-10-01", "2025-04-01", "2024-10-01"])
        df_l = pd.DataFrame({
            "年月": dates,
            "逾放比": [0.035, 0.025, 0.015, 0.010],
            "提撥率": [0.015, 0.016, 0.017, 0.018],
        })
        d = self._make_d(df_l)
        stats = compute_ovd_stats(d)
        assert stats["months_warn"] == 2

    def test_coverage(self):
        dates = pd.to_datetime(["2026-04-01"])
        df_l = pd.DataFrame({
            "年月": dates,
            "逾放比": [0.02],
            "提撥率": [0.01],
        })
        d = {"df_l": df_l}
        stats = compute_ovd_stats(d)
        assert stats["coverage"] == 0.5

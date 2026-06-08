import numpy as np
import pandas as pd
from common.cleaning import normalize_html_percentage, defensive_clean_value, defensive_clean_series


class TestNormalizeHtmlPercentage:
    def test_percentage_field_division(self):
        assert normalize_html_percentage("45.0", "貸放比") == 0.45
        assert normalize_html_percentage("85.5", "儲蓄率") == 0.855

    def test_non_percentage_field(self):
        assert normalize_html_percentage("12345", "社員數") == 12345

    def test_nbsp_returns_nan(self):
        result = normalize_html_percentage("&nbsp;", "貸放比")
        assert np.isnan(result)

    def test_empty_string_returns_nan(self):
        result = normalize_html_percentage("", "貸放比")
        assert np.isnan(result)

    def test_nan_string_returns_nan(self):
        result = normalize_html_percentage("nan", "貸放比")
        assert np.isnan(result)

    def test_provision_no_overdue(self):
        result = normalize_html_percentage("無逾期", "提撥率")
        assert result == "無逾期"

    def test_comma_and_currency_stripped(self):
        assert normalize_html_percentage("NT$1,234,567", "社員數") == 1234567

    def test_percentage_sign_stripped(self):
        assert normalize_html_percentage("5.5%", "逾放比") == 0.055
        assert normalize_html_percentage("95%", "收支比") == 0.95

    def test_invalid_string_returns_raw(self):
        assert normalize_html_percentage("abc", "貸放比") == "abc"


class TestDefensiveCleanValue:
    def test_nat_passed_through(self):
        result = defensive_clean_value(pd.NaT, "貸放比")
        assert pd.isna(result)

    def test_none_passed_through(self):
        assert defensive_clean_value(None, "貸放比") is None

    def test_ovd_and_provision_untouched(self):
        assert defensive_clean_value(0.05, "逾放比") == 0.05
        assert defensive_clean_value(0.02, "提撥率") == 0.02

    def test_loan_ratio_normal(self):
        assert defensive_clean_value(0.45, "貸放比") == 0.45

    def test_loan_ratio_over_one_divided(self):
        assert defensive_clean_value(45.0, "貸放比") == 0.45

    def test_savings_rate_normal(self):
        assert defensive_clean_value(0.85, "儲蓄率") == 0.85

    def test_savings_rate_over_one_divided(self):
        assert defensive_clean_value(85.0, "儲蓄率") == 0.85

    def test_expense_ratio_normal(self):
        assert defensive_clean_value(0.95, "開支比") == 0.95

    def test_expense_ratio_over_five_divided(self):
        assert defensive_clean_value(95.0, "開支比") == 0.95

    def test_unparseable_string_returns_original(self):
        assert defensive_clean_value("N/A", "貸放比") == "N/A"


class TestDefensiveCleanSeries:
    def test_series_cleaning(self):
        s = pd.Series([45.0, 0.50, 0.55, 0.52])
        result = defensive_clean_series(s, "貸放比")
        expected = [0.45, 0.50, 0.55, 0.52]
        pd.testing.assert_series_equal(pd.Series(expected), result)

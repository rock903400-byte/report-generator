import pandas as pd
import pytest
from common.utils import safe_div, format_large_number, fmt_pct


class TestSafeDiv:
    def test_normal_division(self):
        assert safe_div(10, 5) == 2.0

    def test_zero_denominator(self):
        assert safe_div(10, 0) == 0.0

    def test_nan_denominator(self):
        assert safe_div(10, pd.NA) == 0.0

    def test_none_denominator(self):
        assert safe_div(10, None) == 0.0

    def test_zero_numerator(self):
        assert safe_div(0, 5) == 0.0

    def test_negative_values(self):
        assert safe_div(-10, 5) == -2.0

    def test_both_zero(self):
        assert safe_div(0, 0) == 0.0

    def test_float_result(self):
        assert safe_div(1, 3) == pytest.approx(0.333333, rel=1e-5)

    def test_string_numerator(self):
        assert safe_div("abc", 5) == 0.0


class TestFormatLargeNumber:
    def test_hundred_millions(self):
        assert format_large_number(150_000_000) == "1.50 億元"
        assert format_large_number(150_000_000, 1) == "1.5 億元"

    def test_ten_thousands(self):
        assert format_large_number(50_000) == "5 萬元"
        assert format_large_number(9_999) == "9,999 元"

    def test_small_number(self):
        assert format_large_number(500) == "500 元"

    def test_negative_large(self):
        result = format_large_number(-5_000_000)
        assert "萬元" in result

    def test_zero(self):
        assert format_large_number(0) == "0 元"

    def test_float_input(self):
        assert format_large_number(1.5e8) == "1.50 億元"

    def test_invalid_string(self):
        assert format_large_number("abc") == "abc"


class TestFmtPct:
    def test_normal(self):
        assert fmt_pct(0.056) == "5.6%"

    def test_one_hundred_percent(self):
        assert fmt_pct(1.0) == "100.0%"

    def test_zero(self):
        assert fmt_pct(0) == "0.0%"

    def test_custom_decimals(self):
        assert fmt_pct(0.05678, 3) == "5.678%"

    def test_negative(self):
        assert fmt_pct(-0.05) == "-5.0%"

    def test_invalid_input(self):
        assert fmt_pct("abc") == "—"

    def test_none_input(self):
        assert fmt_pct(None) == "—"

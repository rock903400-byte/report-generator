import pandas as pd
from common.dates import convert_minguo_date, get_value


class TestConvertMinguoDate:
    def test_five_digit_date(self):
        result = convert_minguo_date(11504)
        assert result == pd.Timestamp("2026-04-01")

    def test_five_digit_string_date(self):
        result = convert_minguo_date("11504")
        assert result == pd.Timestamp("2026-04-01")

    def test_four_digit_date(self):
        result = convert_minguo_date(5104)
        assert result == pd.Timestamp("1962-04-01")

    def test_three_digit_returns_nat(self):
        result = convert_minguo_date(999)
        assert pd.isna(result)

    def test_six_digit_returns_nat(self):
        result = convert_minguo_date(115041)
        assert pd.isna(result)

    def test_empty_string_returns_nat(self):
        result = convert_minguo_date("")
        assert pd.isna(result)

    def test_non_numeric_returns_nat(self):
        result = convert_minguo_date("abc")
        assert pd.isna(result)

    def test_float_numeric(self):
        result = convert_minguo_date(11504.0)
        assert result == pd.Timestamp("2026-04-01")

    def test_january_handling(self):
        result = convert_minguo_date(11501)
        assert result == pd.Timestamp("2026-01-01")

    def test_december_handling(self):
        result = convert_minguo_date(11512)
        assert result == pd.Timestamp("2026-12-01")


class TestGetValue:
    def test_normal_case(self):
        df = pd.DataFrame({
            "年月": pd.to_datetime(["2026-02-01", "2026-03-01", "2026-04-01"]),
            "社員數": [220, 215, 210],
        })
        result = get_value(df, "社員數", pd.Timestamp("2026-03-15"))
        assert result == 215.0

    def test_exact_boundary(self):
        df = pd.DataFrame({
            "年月": pd.to_datetime(["2026-03-01", "2026-04-01"]),
            "社員數": [215, 210],
        })
        result = get_value(df, "社員數", pd.Timestamp("2026-03-01"))
        assert result == 215.0

    def test_before_all_dates(self):
        df = pd.DataFrame({
            "年月": pd.to_datetime(["2026-04-01", "2026-05-01"]),
            "社員數": [210, 215],
        })
        result = get_value(df, "社員數", pd.Timestamp("2026-01-01"))
        assert result == 210.0

    def test_after_all_dates(self):
        df = pd.DataFrame({
            "年月": pd.to_datetime(["2026-03-01", "2026-04-01"]),
            "社員數": [215, 210],
        })
        result = get_value(df, "社員數", pd.Timestamp("2026-06-01"))
        assert result == 210.0

    def test_empty_df(self):
        df = pd.DataFrame({"年月": pd.Series(dtype="datetime64[ns]"), "社員數": pd.Series(dtype="float64")})
        result = get_value(df, "社員數", pd.Timestamp("2026-04-01"))
        assert result == 0.0

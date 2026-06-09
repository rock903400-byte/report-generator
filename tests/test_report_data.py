import pytest
import pandas as pd

# ── _clean_excel ────────────────────────────────────────────────


def _build_raw_dfs():
    df_m = pd.DataFrame(
        {
            "年月": ["11504", "11412", "11312"],
            "社號": ["3403", "3403", "3403"],
            "社名": ["海星", "海星", "海星"],
            "社員數": ["230", "225", "220"],
            "股金": ["7e7", "6.5e7", "6e7"],
            "貸放比": ["0.55", "0.52", "0.50"],
            "儲蓄率": ["0.89", "0.88", "0.87"],
        }
    )
    df_l = pd.DataFrame(
        {
            "年月": ["11504", "11412", "11312"],
            "社號": ["3403", "3403", "3403"],
            "社名": ["海星", "海星", "海星"],
            "開支比": ["0.98", "0.96", "0.97"],
            "逾放比": ["0.035", "0.04", "0.05"],
            "逾期貸款": ["250e4", "255e4", "270e4"],
            "提撥率": ["0.015", "0.016", "0.017"],
        }
    )
    return df_m, df_l


def test_clean_excel_converts_dates():
    from report_data import _clean_excel

    df_m, df_l = _build_raw_dfs()
    cm, cl = _clean_excel(df_m, df_l)
    assert pd.api.types.is_datetime64_any_dtype(cm["年月"])
    assert pd.api.types.is_datetime64_any_dtype(cl["年月"])


def test_clean_excel_numeric_columns():
    from report_data import _clean_excel

    df_m, df_l = _build_raw_dfs()
    cm, cl = _clean_excel(df_m, df_l)
    for col in ["社員數", "股金", "貸放比"]:
        assert pd.api.types.is_numeric_dtype(cm[col])
    assert pd.api.types.is_numeric_dtype(cl["逾放比"])
    assert pd.api.types.is_numeric_dtype(cl["逾期貸款"])


def test_clean_excel_drops_invalid_dates():
    from report_data import _clean_excel

    df_m_bad = pd.DataFrame(
        {
            "年月": ["invalid", "11412"],
            "社號": ["3403", "3403"],
            "社名": ["海星", "海星"],
            "社員數": [100, 200],
            "股金": [1e7, 2e7],
            "貸放比": [0.3, 0.4],
            "儲蓄率": [0.7, 0.8],
        }
    )
    df_l_good = _build_raw_dfs()[1]
    cm, _ = _clean_excel(df_m_bad, df_l_good)
    assert len(cm) == 1
    assert cm["年月"].iloc[0] == pd.to_datetime("2025-12-01")


# ── load_data_from_bytes ───────────────────────────────────────


def test_load_data_from_bytes(sample_excel_bytes):
    from report_data import load_data_from_bytes

    df_m, df_l, df_csv = load_data_from_bytes(sample_excel_bytes)
    assert len(df_m) > 0
    assert len(df_l) > 0
    assert "社員數" in df_m.columns
    assert "開支比" in df_l.columns


def test_load_data_from_bytes_missing_sheet():
    from report_data import load_data_from_bytes
    import io
    import pandas as pd

    bad_buf = io.BytesIO()
    pd.DataFrame({"a": [1]}).to_excel(bad_buf, sheet_name="WrongSheet", index=False)
    bad_buf.seek(0)

    with pytest.raises(Exception):
        load_data_from_bytes(bad_buf.read())


def test_load_data_from_bytes_with_csv(sample_excel_bytes):
    import io
    from report_data import load_data_from_bytes

    csv_content = "年月,社號,社名,會計科目,會科名稱,當月金額\n11504,3403,海星,1311,放款,35180000\n11412,3403,海星,1311,放款,36030000\n"
    csv_bytes = io.BytesIO(csv_content.encode("utf-8-sig"))

    df_m, df_l, df_csv = load_data_from_bytes(sample_excel_bytes, csv_bytes.getvalue())
    assert not df_csv.empty
    assert "當月金額" in df_csv.columns


# ── extract_union_data ─────────────────────────────────────────


def test_extract_union_data(sample_excel_bytes):
    from report_data import load_data_from_bytes, extract_union_data

    df_m, df_l, df_csv = load_data_from_bytes(sample_excel_bytes)
    d = extract_union_data(df_m, df_l, df_csv, "3403")
    assert d["s_name"] == "海星"
    assert d["s_no"] == "3403"
    assert d["M0"] > 0
    assert d["S0"] > 0
    assert "status" in d
    assert "notes" in d
    assert "risk_count" in d


def test_extract_union_data_not_found(sample_excel_bytes):
    from report_data import load_data_from_bytes, extract_union_data

    df_m, df_l, df_csv = load_data_from_bytes(sample_excel_bytes)
    with pytest.raises(ValueError, match="社號 9999 在社務資料中無數據"):
        extract_union_data(df_m, df_l, df_csv, "9999")


# ── compute_ovd_stats ──────────────────────────────────────────


def test_compute_ovd_stats(sample_excel_bytes):
    from report_data import load_data_from_bytes, extract_union_data, compute_ovd_stats

    df_m, df_l, df_csv = load_data_from_bytes(sample_excel_bytes)
    d = extract_union_data(df_m, df_l, df_csv, "3403")
    stats = compute_ovd_stats(d)
    assert "curr" in stats
    assert "avg12" in stats
    assert "trend" in stats
    assert "months_total" in stats
    assert stats["months_total"] > 0


def test_compute_ovd_stats_empty():
    from report_data import compute_ovd_stats

    d = {
        "df_l": pd.DataFrame(),
    }
    stats = compute_ovd_stats(d)
    assert stats["curr"] == 0
    assert stats["trend"] == "無資料"
    assert stats["prov_note"] == ""


# ── eProv_note ─────────────────────────────────────────────────


def test_extract_union_data_eProv_note_normal():
    from report_data import _clean_excel, extract_union_data

    df_m = pd.DataFrame(
        {
            "年月": ["11504"],
            "社號": ["3403"],
            "社名": ["海星"],
            "社員數": ["230"],
            "股金": ["7e7"],
            "貸放比": ["0.55"],
            "儲蓄率": ["0.89"],
        }
    )
    df_l = pd.DataFrame(
        {
            "年月": ["11504"],
            "社號": ["3403"],
            "社名": ["海星"],
            "開支比": ["0.98"],
            "逾放比": ["0.035"],
            "逾期貸款": ["250e4"],
            "提撥率": ["0.015"],
        }
    )
    cm, cl = _clean_excel(df_m, df_l)
    d = extract_union_data(cm, cl, pd.DataFrame(), "3403")
    assert d["eProv_note"] == ""


def test_extract_union_data_eProv_note_no_ovd():
    from report_data import _clean_excel, extract_union_data

    df_m = pd.DataFrame(
        {
            "年月": ["11504"],
            "社號": ["3403"],
            "社名": ["海星"],
            "社員數": ["230"],
            "股金": ["7e7"],
            "貸放比": ["0.55"],
            "儲蓄率": ["0.89"],
        }
    )
    df_l = pd.DataFrame(
        {
            "年月": ["11504"],
            "社號": ["3403"],
            "社名": ["海星"],
            "開支比": ["0.98"],
            "逾放比": ["0"],
            "逾期貸款": ["0"],
            "提撥率": ["0"],
        }
    )
    cm, cl = _clean_excel(df_m, df_l)
    d = extract_union_data(cm, cl, pd.DataFrame(), "3403")
    assert d["eProv_note"] == "無逾期"


def test_extract_union_data_eProv_note_missing():
    from report_data import _clean_excel, extract_union_data

    df_m = pd.DataFrame(
        {
            "年月": ["11504"],
            "社號": ["3403"],
            "社名": ["海星"],
            "社員數": ["230"],
            "股金": ["7e7"],
            "貸放比": ["0.55"],
            "儲蓄率": ["0.89"],
        }
    )
    df_l = pd.DataFrame(
        {
            "年月": ["11504"],
            "社號": ["3403"],
            "社名": ["海星"],
            "開支比": ["0.98"],
            "逾放比": ["0.035"],
            "逾期貸款": ["250e4"],
            "提撥率": [None],
        }
    )
    cm, cl = _clean_excel(df_m, df_l)
    d = extract_union_data(cm, cl, pd.DataFrame(), "3403")
    assert d["eProv_note"] == "資料缺失"


def test_compute_ovd_stats_prov_note():
    from report_data import compute_ovd_stats

    df_l = pd.DataFrame(
        {
            "年月": pd.to_datetime(["2026-04-01", "2025-12-01"]),
            "逾放比": [0.0, 0.0],
            "提撥率": [0.0, 0.0],
            "提撥率_缺失": [False, False],
        }
    )
    d = {"df_l": df_l}
    stats = compute_ovd_stats(d)
    assert stats["prov_note"] == "無逾期"

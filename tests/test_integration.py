import pytest
import pandas as pd
from report_data import load_data_from_bytes, extract_union_data
from report_charts import generate_all_charts
from report_html import build_report


class TestFullPipeline:
    """End-to-end: Excel bytes → dict → charts → HTML"""

    def test_full_pipeline_with_sample_data(self, sample_excel_bytes):
        df_m, df_l, df_csv = load_data_from_bytes(sample_excel_bytes)
        assert not df_m.empty
        assert not df_l.empty

        d = extract_union_data(df_m, df_l, df_csv, "3403")
        assert d["s_name"] == "海星"
        assert d["s_no"] == "3403"
        assert d["max_d"] is not None

        charts = generate_all_charts(d)
        assert isinstance(charts, dict)
        assert len(charts) == 9

        html = build_report(d, charts)
        assert '<!DOCTYPE html>' in html
        assert '海星' in html
        assert '3403' in html
        assert 'kpi-card' in html

    def test_pipeline_without_csv(self, sample_excel_bytes):
        df_m, df_l, df_csv = load_data_from_bytes(sample_excel_bytes, csv_bytes=None)
        d = extract_union_data(df_m, df_l, df_csv, "3403")
        charts = generate_all_charts(d)
        html = build_report(d, charts, ai_analysis=None)
        assert '無 CSV 財務資料' in charts["waterfall"]
        assert 'AI 顧問分析' not in html

    def test_pipeline_multiple_unions(self, sample_excel_bytes):
        df_m, df_l, df_csv = load_data_from_bytes(sample_excel_bytes)
        with pytest.raises(ValueError, match="無數據"):
            extract_union_data(df_m, df_l, df_csv, "9999")

    def test_pipeline_all_charts_are_html(self, sample_excel_bytes):
        df_m, df_l, df_csv = load_data_from_bytes(sample_excel_bytes)
        d = extract_union_data(df_m, df_l, df_csv, "3403")
        charts = generate_all_charts(d)
        for key, val in charts.items():
            assert isinstance(val, str), f"{key} is not str, got {type(val)}"

    def test_pipeline_html_contains_chart_divs(self, sample_excel_bytes):
        df_m, df_l, df_csv = load_data_from_bytes(sample_excel_bytes)
        d = extract_union_data(df_m, df_l, df_csv, "3403")
        charts = generate_all_charts(d)
        html = build_report(d, charts)
        assert '逾放比深度分析' in html
        assert '財務科目分析' in html
        assert '近 12 期' in html

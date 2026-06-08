import pandas as pd
import pytest
from datetime import date
from report_html import (
    _inline_md, _md_to_html, _is_ai_truncated,
    df_to_html_table, build_kpi_yoy_table, build_report,
    PLOTLY_JS_CDN,
)


class TestInlineMd:
    def test_bold(self):
        assert _inline_md("**粗體**") == "<strong>粗體</strong>"

    def test_italic(self):
        assert _inline_md("*斜體*") == "<em>斜體</em>"

    def test_combined(self):
        result = _inline_md("**粗體** 和 *斜體*")
        assert "<strong>粗體</strong>" in result
        assert "<em>斜體</em>" in result

    def test_html_escaped(self):
        result = _inline_md("<script>alert('xss')</script>")
        assert "&lt;" in result
        assert "<script>" not in result

    def test_not_bold_single_asterisk(self):
        """Single * not at word boundary shouldn't be treated as italic"""
        result = _inline_md("not*italic")
        assert "<em>" not in result

    def test_no_markdown(self):
        assert _inline_md("plain text") == "plain text"


class TestMdToHtml:
    def test_empty_string(self):
        assert _md_to_html("") == ""

    def test_whitespace_only(self):
        assert _md_to_html("  \n  ") == ""

    def test_heading_h3(self):
        result = _md_to_html("# Title")
        assert "<h3>Title</h3>" in result

    def test_heading_h4(self):
        result = _md_to_html("## Section")
        assert "<h4>Section</h4>" in result

    def test_unordered_list(self):
        md = "- item 1\n- item 2"
        result = _md_to_html(md)
        assert "<ul>" in result
        assert "<li>item 1</li>" in result
        assert "<li>item 2</li>" in result
        assert "</ul>" in result

    def test_ordered_list(self):
        md = "1. first\n2. second"
        result = _md_to_html(md)
        assert "<ol>" in result
        assert "<li>first</li>" in result
        assert "<li>second</li>" in result
        assert "</ol>" in result

    def test_paragraph(self):
        result = _md_to_html("Hello world")
        assert "<p>Hello world</p>" in result

    def test_multiline_paragraph(self):
        md = "line one\nline two"
        result = _md_to_html(md)
        assert "<p>line one line two</p>" in result

    def test_mixed_content(self):
        md = "# Header\n\n- item 1\n- item 2\n\nparagraph text"
        result = _md_to_html(md)
        assert "<h3>Header</h3>" in result
        assert "<li>item 1</li>" in result
        assert "<p>paragraph text</p>" in result

    def test_markdown_in_list(self):
        md = "- **bold** item"
        result = _md_to_html(md)
        assert "<strong>bold</strong>" in result

    def test_switch_from_ol_to_ul(self):
        md = "1. first\n- second"
        result = _md_to_html(md)
        assert "<ol>" in result
        assert "<ul>" in result

    def test_switch_from_ul_to_ol(self):
        md = "- first\n1. second"
        result = _md_to_html(md)
        assert "<ul>" in result
        assert "<ol>" in result


class TestIsAiTruncated:
    def test_none_or_empty(self):
        assert _is_ai_truncated(None) is True
        assert _is_ai_truncated("") is True
        assert _is_ai_truncated("  ") is True

    def test_unclosed_bold(self):
        assert _is_ai_truncated("some text **") is True

    def test_unclosed_italic(self):
        assert _is_ai_truncated("some text *") is True

    def test_ends_with_dash(self):
        assert _is_ai_truncated("text -") is True

    def test_ends_with_colon(self):
        assert _is_ai_truncated("text：") is True

    def test_complete_text(self):
        assert _is_ai_truncated("完整內容。") is False

    def test_complete_with_list(self):
        assert _is_ai_truncated("- 亮點：無\n- 建議：增資") is False


class TestDfToHtmlTable:
    def test_returns_table(self):
        df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        html = df_to_html_table(df)
        assert "<table" in html
        assert "</table>" in html

    def test_headers_present(self):
        df = pd.DataFrame({"姓名": ["王小明"], "年齡": [30]})
        html = df_to_html_table(df)
        assert "姓名" in html
        assert "年齡" in html

    def test_data_present(self):
        df = pd.DataFrame({"X": ["a"], "Y": ["b"]})
        html = df_to_html_table(df)
        assert "a" in html
        assert "b" in html

    def test_class_attribute(self):
        df = pd.DataFrame({"A": [1]})
        html = df_to_html_table(df)
        assert 'class="data-table"' in html


class TestBuildKpiYoyTable:
    def test_insufficient_data(self):
        df_m = pd.DataFrame({
            "年月": pd.to_datetime(["2026-04-01"]),
            "社員數": [210], "股金": [5e7], "貸放比": [0.45], "儲蓄率": [0.85],
        })
        df_l = pd.DataFrame({
            "年月": pd.to_datetime(["2026-04-01"]),
            "逾放比": [0.03], "開支比": [0.95], "提撥率": [0.015], "逾期貸款": [2.5e6],
        })
        d = {"df_m": df_m, "df_l": df_l}
        result = build_kpi_yoy_table(d)
        assert '年度資料不足' in result

    def test_two_years_of_data(self):
        df_m = pd.DataFrame({
            "年月": pd.to_datetime(["2025-12-01", "2024-12-01"]),
            "社員數": [210, 220], "股金": [5e7, 5.5e7],
            "貸放比": [0.45, 0.48], "儲蓄率": [0.85, 0.86],
        })
        df_l = pd.DataFrame({
            "年月": pd.to_datetime(["2025-12-01", "2024-12-01"]),
            "逾放比": [0.03, 0.04], "開支比": [0.95, 0.96],
            "提撥率": [0.015, 0.016], "逾期貸款": [2.5e6, 2.6e6],
        })
        d = {"df_m": df_m, "df_l": df_l}
        result = build_kpi_yoy_table(d)
        assert '<table' in result
        assert '民114' in result
        assert '民113' in result
        assert '社員數' in result
        assert '貸放比' in result
        assert '逾放比' in result

    def test_with_csv_lending_rate(self):
        df_m = pd.DataFrame({
            "年月": pd.to_datetime(["2025-12-01", "2024-12-01"]),
            "社員數": [210, 220], "股金": [5e7, 5.5e7],
            "貸放比": [0.45, 0.48], "儲蓄率": [0.85, 0.86],
        })
        df_l = pd.DataFrame({
            "年月": pd.to_datetime(["2025-12-01", "2024-12-01"]),
            "逾放比": [0.03, 0.04], "開支比": [0.95, 0.96],
            "提撥率": [0.015, 0.016], "逾期貸款": [2.5e6, 2.6e6],
        })
        months = pd.date_range("2025-01-01", "2025-12-01", freq="MS")
        rows = []
        for m in months:
            rows.append([m, "4101", "利息收入", 50000])
            rows.append([m, "1311", "短期放款", 3e7])
        df_csv = pd.DataFrame(rows, columns=["年月", "會計科目", "會科名稱", "當月金額"])
        df_csv["年月"] = pd.to_datetime(df_csv["年月"])
        df_csv["當月金額"] = df_csv["當月金額"].astype(float)
        d = {"df_m": df_m, "df_l": df_l, "has_csv": True, "df_csv": df_csv}
        result = build_kpi_yoy_table(d)
        assert '放款利率' in result


class TestBuildReport:
    def _make_d(self):
        dates = pd.to_datetime(["2026-04-01", "2025-12-01", "2025-06-01", "2024-12-01"])
        df_m = pd.DataFrame({
            "年月": dates,
            "社員數": [205, 208, 210, 215],
            "股金": [4.8e7, 5.0e7, 5.2e7, 5.5e7],
            "貸放比": [0.42, 0.44, 0.46, 0.48],
            "儲蓄率": [0.83, 0.84, 0.85, 0.86],
        })
        df_l = pd.DataFrame({
            "年月": dates,
            "逾放比": [0.035, 0.032, 0.030, 0.028],
            "開支比": [0.95, 0.96, 0.94, 0.93],
            "逾期貸款": [2.8e6, 2.7e6, 2.6e6, 2.5e6],
            "提撥率": [0.015, 0.016, 0.016, 0.017],
        })
        return dict(
            s_name="海星", s_no="3403",
            max_d=dates[-1],
            df_m=df_m, df_l=df_l,
            T0=pd.Timestamp("2025-12-01"),
            T1=pd.Timestamp("2024-12-01"),
            eLoan=0.42, eRate=0.83, eOvd=0.035, eProv=0.015,
            R0=0.95, R1=0.96,
            curr_M=205, M0=208, M1=210, M2=215, M3=220,
            curr_S=4.8e7, S0=5.0e7, S1=5.2e7, S2=5.5e7, S3=5.8e7,
            memG_curr=-0.014, shrG_curr=-0.04,
            status="📊 一般狀態", status_color="#64748B",
            reason_text="各指標平穩", notes=[], risk_count=0,
        )

    def test_returns_complete_html(self):
        d = self._make_d()
        charts = {"member_capital_trend": "<div>chart</div>"}
        html = build_report(d, charts)
        assert '<!DOCTYPE html>' in html
        assert '</html>' in html
        assert '海星' in html
        assert '3403' in html
        assert 'data-table' in html

    def test_with_ai_analysis(self):
        d = self._make_d()
        charts = {"member_capital_trend": "<div>chart</div>"}
        html = build_report(d, charts, ai_analysis="**分析**：良好")
        assert 'AI 顧問分析' in html
        assert '<strong>分析</strong>' in html

    def test_with_truncated_ai(self):
        d = self._make_d()
        charts = {"member_capital_trend": "<div>chart</div>"}
        html = build_report(d, charts, ai_analysis="部分內容**")
        assert '截斷' in html or '不完整' in html

    def test_without_ai(self):
        d = self._make_d()
        charts = {"member_capital_trend": "<div>chart</div>"}
        html = build_report(d, charts)
        assert 'AI 顧問分析' not in html

    def test_kpi_cards_present(self):
        d = self._make_d()
        charts = {"member_capital_trend": "<div>chart</div>"}
        html = build_report(d, charts)
        assert '風險觸發數' in html
        assert '現有社員' in html
        assert '貸放比' in html
        assert '逾放比' in html

    def test_risk_section_present(self):
        d = self._make_d()
        charts = {"member_capital_trend": "<div>chart</div>"}
        html = build_report(d, charts)
        assert '風險診斷摘要' in html

    def test_ovd_stats_section(self):
        d = self._make_d()
        charts = {"member_capital_trend": "<div>chart</div>"}
        html = build_report(d, charts)
        assert '最新逾放比' in html

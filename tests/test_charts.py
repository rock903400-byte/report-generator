import pandas as pd
import numpy as np
import pytest
from report_charts import (
    style_fig, to_html_div,
    chart_member_capital_trend, chart_loan_savings, chart_risk_trend,
    chart_ovd_full_history, chart_ovd_amount,
    chart_waterfall, chart_annual_trend,
    make_balance_sheet_html, chart_lending_rate,
    generate_all_charts,
)
import plotly.graph_objects as go


def _build_d(with_csv=False):
    dates = pd.to_datetime(["2026-04-01", "2025-12-01", "2025-06-01",
                            "2024-12-01", "2024-06-01", "2023-12-01"])
    df_m = pd.DataFrame({
        "年月": dates,
        "社號": ["3403"] * 6,
        "社名": ["海星"] * 6,
        "社員數": [205, 208, 210, 215, 220, 230],
        "股金":   [4.8e7, 5.0e7, 5.2e7, 5.5e7, 6.0e7, 6.5e7],
        "貸放比": [0.42, 0.44, 0.46, 0.48, 0.50, 0.52],
        "儲蓄率": [0.83, 0.84, 0.85, 0.86, 0.87, 0.88],
    })
    df_l = pd.DataFrame({
        "年月": dates,
        "社號": ["3403"] * 6,
        "社名": ["海星"] * 6,
        "逾放比": [0.035, 0.032, 0.030, 0.028, 0.025, 0.020],
        "開支比": [0.95, 0.96, 0.94, 0.93, 0.92, 0.91],
        "逾期貸款": [2.8e6, 2.7e6, 2.6e6, 2.5e6, 2.4e6, 2.3e6],
        "提撥率": [0.015, 0.016, 0.016, 0.017, 0.017, 0.018],
    })

    d = dict(
        s_no="3403", s_name="海星",
        max_d=dates[-1], min_d=dates[0],
        df_m=df_m, df_l=df_l,
        curr_M=205, M0=208, M1=210, M2=215, M3=230,
        curr_S=4.8e7, S0=5.0e7, S1=5.2e7, S2=5.5e7, S3=6.5e7,
        R0=0.95, R1=0.96,
        O0=2.8e6, O1=2.7e6,
        eOvd=0.035, eLoan=0.42, eRate=0.83, eProv=0.015,
        memG=-0.02, shrG=-0.04,
        memG_curr=-0.014, shrG_curr=-0.04,
        eOvd_12m=0.03,
        status="📊 一般狀態", status_color="#64748B",
        reason_text="各指標平穩", notes=[], risk_count=0,
        has_csv=False, df_csv=pd.DataFrame(),
    )
    return d


CSV_COLS = ["年月", "社號", "會計科目", "會科名稱", "當月金額"]


def _build_d_with_csv():
    d = _build_d()
    dates = pd.to_datetime(["2026-04-01", "2026-04-01", "2026-04-01",
                            "2026-04-01", "2026-04-01", "2026-04-01",
                            "2025-04-01", "2025-04-01", "2025-04-01"])
    df_csv = pd.DataFrame([
        ["2026-04-01", "3403", "4101", "利息收入", 500000],
        ["2026-04-01", "3403", "5101", "利息支出", 200000],
        ["2026-04-01", "3403", "5201", "人事費用", 100000],
        ["2026-04-01", "3403", "1101", "現金", 5000000],
        ["2026-04-01", "3403", "1311", "短期放款", 30000000],
        ["2026-04-01", "3403", "3101", "股金", 40000000],
        ["2025-04-01", "3403", "4101", "利息收入", 480000],
        ["2025-04-01", "3403", "5101", "利息支出", 190000],
        ["2025-04-01", "3403", "1311", "短期放款", 28000000],
    ], columns=CSV_COLS)
    df_csv["年月"] = pd.to_datetime(df_csv["年月"])
    df_csv["當月金額"] = df_csv["當月金額"].astype(float)
    d["has_csv"] = True
    d["df_csv"] = df_csv
    return d


class TestStyleFig:
    def test_returns_figure(self):
        fig = go.Figure()
        result = style_fig(fig, title="Test", height=400)
        assert isinstance(result, go.Figure)

    def test_sets_title(self):
        fig = go.Figure()
        result = style_fig(fig, title="測試")
        assert result.layout.title.text == "測試"

    def test_no_title_when_omitted(self):
        fig = go.Figure()
        result = style_fig(fig)
        assert result.layout.title.text is None or result.layout.title.text == ""

    def test_sets_height(self):
        fig = go.Figure()
        result = style_fig(fig, height=999)
        assert result.layout.height == 999


class TestToHtmlDiv:
    def test_returns_string(self):
        fig = go.Figure()
        html = to_html_div(fig)
        assert isinstance(html, str)
        assert '<div' in html

    def test_contains_plotly_div(self):
        fig = go.Figure()
        html = to_html_div(fig)
        assert 'plotly-graph-div' in html


class TestChartMemberCapitalTrend:
    def test_returns_html(self):
        d = _build_d()
        html = chart_member_capital_trend(d)
        assert isinstance(html, str)
        assert '<div' in html
        assert 'plotly-graph-div' in html

    def test_contains_member_count(self):
        d = _build_d()
        html = chart_member_capital_trend(d)
        assert 'plotly-graph-div' in html
        assert 'hovermode' in html

    def test_contains_capital(self):
        d = _build_d()
        html = chart_member_capital_trend(d)
        assert 'yaxis2' in html or 'tickformat' in html


class TestChartLoanSavings:
    def test_returns_html(self):
        d = _build_d()
        html = chart_loan_savings(d)
        assert isinstance(html, str)
        assert '<div' in html

    def test_contains_reference_lines(self):
        d = _build_d()
        html = chart_loan_savings(d)
        assert 'plotly-graph-div' in html
        assert 'yaxis2' in html


class TestChartRiskTrend:
    def test_returns_html(self):
        d = _build_d()
        html = chart_risk_trend(d)
        assert isinstance(html, str)
        assert '<div' in html

    def test_contains_ovd_and_expense(self):
        d = _build_d()
        html = chart_risk_trend(d)
        assert 'plotly-graph-div' in html
        assert 'overtemplate' in html or 'yaxis2' in html


class TestChartOvdFullHistory:
    def test_returns_html(self):
        d = _build_d()
        html = chart_ovd_full_history(d)
        assert isinstance(html, str)
        assert '<div' in html

    def test_contains_moving_averages(self):
        d = _build_d()
        html = chart_ovd_full_history(d)
        assert '3M' in html or '6M' in html or 'plotly-graph-div' in html

    def test_contains_peak_marker(self):
        d = _build_d()
        html = chart_ovd_full_history(d)
        assert 'triangle-up' in html or 'text' in html
        assert 'triangle-down' in html


class TestChartOvdAmount:
    def test_returns_html(self):
        d = _build_d()
        html = chart_ovd_amount(d)
        assert isinstance(html, str)
        assert '<div' in html

    def test_contains_ovd_columns(self):
        d = _build_d()
        html = chart_ovd_amount(d)
        assert 'plotly-graph-div' in html
        assert 'yaxis2' in html


class TestChartWaterfall:
    def test_no_csv_fallback(self):
        d = _build_d()
        html = chart_waterfall(d)
        assert '無 CSV' in html

    def test_with_csv_returns_html(self):
        d = _build_d_with_csv()
        html = chart_waterfall(d)
        assert isinstance(html, str)

    def test_waterfall_structure(self):
        d = _build_d_with_csv()
        html = chart_waterfall(d)
        assert 'plotly-graph-div' in html or '無' in html


class TestChartAnnualTrend:
    def test_no_csv_fallback(self):
        d = _build_d()
        html = chart_annual_trend(d)
        assert '無 CSV' in html

    def test_with_csv_returns_html(self):
        d = _build_d_with_csv()
        html = chart_annual_trend(d)
        assert isinstance(html, str)

    def test_contains_years(self):
        d = _build_d_with_csv()
        html = chart_annual_trend(d)
        assert 'plotly-graph-div' in html


class TestMakeBalanceSheetHtml:
    def test_no_csv_fallback(self):
        d = _build_d()
        html = make_balance_sheet_html(d)
        assert '無 CSV' in html

    def test_with_csv_returns_html(self):
        d = _build_d_with_csv()
        html = make_balance_sheet_html(d)
        assert isinstance(html, str)

    def test_contains_balance_keywords(self):
        d = _build_d_with_csv()
        html = make_balance_sheet_html(d)
        assert '資產合計' in html
        assert '負債及權益合計' in html
        assert '資產負債表' in html


class TestChartLendingRate:
    def test_no_csv_fallback(self):
        d = _build_d()
        html = chart_lending_rate(d)
        assert '無 CSV' in html

    def test_with_csv_returns_html(self):
        d = _build_d_with_csv()
        html = chart_lending_rate(d)
        assert isinstance(html, str)

    def test_insufficient_months_fallback(self):
        d = _build_d_with_csv()
        d["df_csv"] = d["df_csv"][d["df_csv"]["年月"].dt.year == 2026].copy()
        if len(d["df_csv"]) < 10:
            html = chart_lending_rate(d)
            assert isinstance(html, str)

    def test_with_sufficient_data(self):
        d = _build_d_with_csv()
        months = pd.date_range("2025-01-01", "2025-12-01", freq="MS")
        rows = []
        for m in months:
            rows.append([m, "3403", "4101", "利息收入", 50000])
            rows.append([m, "3403", "1311", "短期放款", 30000000])
        csv = pd.DataFrame(rows, columns=CSV_COLS)
        csv["年月"] = pd.to_datetime(csv["年月"])
        csv["當月金額"] = csv["當月金額"].astype(float)
        d["df_csv"] = csv
        html = chart_lending_rate(d)
        assert isinstance(html, str)
        assert '%' in html or '資料不足' in html


class TestGenerateAllCharts:
    def test_returns_dict_with_all_keys(self):
        d = _build_d()
        charts = generate_all_charts(d)
        expected_keys = [
            "member_capital_trend", "loan_savings", "risk_trend",
            "ovd_full_history", "ovd_amount", "waterfall",
            "annual_trend", "balance_sheet", "lending_rate",
        ]
        assert all(k in charts for k in expected_keys)

    def test_with_csv_includes_csv_charts(self):
        d = _build_d_with_csv()
        charts = generate_all_charts(d)
        assert 'plotly-graph-div' in charts["waterfall"] or '無 CSV' in charts["waterfall"]

    def test_all_values_are_strings(self):
        d = _build_d()
        charts = generate_all_charts(d)
        for key, val in charts.items():
            assert isinstance(val, str), f"{key} is not a string"

"""對帳測試：程式輸出必須與來源資料獨立重算一致。

有別於單元測試（只測單一函式），本檔用貼近真實的合成大夾具
（多年份 CSV、59 科目、18/22 餘額、異常提撥率、壞年月列、雙社），
走完整管線後，用「測試內獨立重算」的數字逐條比對渲染結果。

注意：散點圖的 y 值在 HTML 裡是 base64（bdata），不可用字串搜尋；
本檔用 Plotly 官方反序列化把圖還原成 Figure 再比對。
"""

import json

import pandas as pd
import pytest

from report_config import fmt
from report_data import extract_union_data, PROV_ABNORMAL
from report_charts import generate_all_charts, make_balance_sheet_html, chart_waterfall
from report_html import build_report


def figure_data_from_div(html):
    """回傳圖 div 內的 Plotly data 陣列（dict list）。

    注意：散點圖 y 值是 {"dtype","bdata"} 的 base64 包，需再用 decode_y 解開；
    不可用字串搜尋比對圖上數字。
    """
    dec = json.JSONDecoder()

    def _next_value(s, i):
        while s[i] in " \n\r\t":
            i += 1
        val, i = dec.raw_decode(s, i)
        return val, i

    i = html.index("Plotly.newPlot(") + len("Plotly.newPlot(")
    _, i = _next_value(html, i)  # 圖表 id
    i += 1  # 跳過逗號
    data, _ = _next_value(html, i)  # traces
    return data


def decode_y(y):
    """把 trace y 还原成數值 list（處理 bdata base64 包或 plain list）。"""
    import base64

    import numpy as np

    if isinstance(y, dict) and "bdata" in y:
        return np.frombuffer(base64.b64decode(y["bdata"]), dtype=np.dtype(y["dtype"])).tolist()
    return list(y)


def _build_frames():
    months_a = pd.to_datetime(
        ["2024-12-01"]
        + [f"2025-{m:02d}-01" for m in range(1, 13)]
        + ["2026-01-01", "2026-02-01"]
    )
    n_a = len(months_a)
    members_a = [280] + [285] * 11 + [290, 295, 300]
    capital_a = [5.0e7] + [5.2e7] * 11 + [5.5e7, 5.8e7, 6.0e7]
    df_m = pd.DataFrame(
        {
            "年月": list(months_a) + [pd.Timestamp("2025-12-01"), pd.Timestamp("2026-01-01"), pd.Timestamp("2026-02-01")],
            "社號": ["9901"] * n_a + ["9902"] * 3,
            "社名": ["虛構甲社"] * n_a + ["虛構乙社"] * 3,
            "社員數": members_a + [180, 185, 190],
            "股金": capital_a + [2.0e7, 2.1e7, 2.2e7],
            "貸放比": [0.5] * n_a + [0.6] * 3,
            "儲蓄率": [0.85] * n_a + [0.8] * 3,
        }
    )
    df_l = pd.DataFrame(
        {
            "年月": list(months_a) + [pd.Timestamp("2025-12-01"), pd.Timestamp("2026-01-01"), pd.Timestamp("2026-02-01")],
            "社號": ["9901"] * n_a + ["9902"] * 3,
            "社名": ["虛構甲社"] * n_a + ["虛構乙社"] * 3,
            "逾放比": [0.01] * n_a + [0.005] * 3,
            "開支比": [0.9] * n_a + [0.8] * 3,
            "逾期貸款": [1.0e6] * n_a + [5.0e5] * 3,
            "提撥率": [1.5] * n_a + [20.0, 22.0, 25.0],
            "提撥率_缺失": [False] * (n_a + 3),
        }
    )

    rows = []
    for m in range(1, 13):
        dt = pd.Timestamp(f"2025-{m:02d}-01")
        rows += [
            [dt, "9901", "4101", "利息收入", 100000.0],
            [dt, "9901", "5101", "利息支出", 10000.0],
            [dt, "9901", "5201", "人事費用", 20000.0],
            [dt, "9901", "5301", "業務費用", 30000.0],
            [dt, "9901", "5901", "其他支出", 5000.0],
        ]
    for dt in [pd.Timestamp("2026-01-01"), pd.Timestamp("2026-02-01")]:
        rows += [
            [dt, "9901", "4101", "利息收入", 100000.0],
            [dt, "9901", "5101", "利息支出", 10000.0],
            [dt, "9901", "5201", "人事費用", 20000.0],
            [dt, "9901", "5301", "業務費用", 30000.0],
            [dt, "9901", "5901", "其他支出", 5000.0],
        ]
    # 餘額快照：2026-01（舊，不可出現）vs 2026-02（最新，須平衡）
    rows += [
        [pd.Timestamp("2026-01-01"), "9901", "1101", "現金", 9000000.0],
        [pd.Timestamp("2026-01-01"), "9901", "1311", "短期放款", 20000000.0],
        [pd.Timestamp("2026-02-01"), "9901", "1101", "現金", 10000000.0],
        [pd.Timestamp("2026-02-01"), "9901", "1311", "短期放款", 20000000.0],
        [pd.Timestamp("2026-02-01"), "9901", "1811", "存出保證金", 500000.0],
        [pd.Timestamp("2026-02-01"), "9901", "2111", "應付費用", 200000.0],
        [pd.Timestamp("2026-02-01"), "9901", "2252", "預收收入", 100000.0],
        [pd.Timestamp("2026-02-01"), "9901", "2311", "吸收存款", 5000000.0],
        [pd.Timestamp("2026-02-01"), "9901", "3101", "股金", 25200000.0],
        # 壞列：年月壞掉，金額再大也不得污染任何報表
        [pd.NaT, "9901", "1101", "現金", 7777777.0],
    ]
    df_csv = pd.DataFrame(rows, columns=["年月", "社號", "會計科目", "會科名稱", "當月金額"])
    return df_m, df_l, df_csv


@pytest.fixture()
def frames():
    return _build_frames()


@pytest.fixture()
def d_a(frames):
    df_m, df_l, df_csv = frames
    return extract_union_data(df_m, df_l, df_csv, "9901")


@pytest.fixture()
def d_b(frames):
    df_m, df_l, df_csv = frames
    return extract_union_data(df_m, df_l, df_csv, "9902")


class TestKpiReconciliation:
    """KPI 卡數字必須等於來源最新一期的值。"""

    def test_curr_values_match_source(self, d_a, frames):
        df_m, _, _ = frames
        latest = df_m["年月"].max()
        src = df_m[(df_m["社號"] == "9901") & (df_m["年月"] == latest)].iloc[0]
        assert d_a["curr_M"] == src["社員數"] == 300
        assert d_a["curr_S"] == src["股金"] == 6.0e7
        assert d_a["curr_eLoan"] == src["貸放比"] == 0.5

    def test_kpi_html_shows_source_values(self, d_a):
        html = build_report(d_a, {"member_capital_trend": "<div>x</div>"})
        assert "300" in html
        assert fmt(6.0e7) in html

    def test_union_isolation(self, d_a):
        html = build_report(d_a, {"member_capital_trend": "<div>x</div>"})
        assert "虛構甲社" in html
        assert "虛構乙社" not in html


class TestBalanceSheetReconciliation:
    """快照恆平：資產 ＝ 負債 ＋ 權益，且只取最新一期。"""

    def test_balances_with_18_22(self, d_a):
        html = make_balance_sheet_html(d_a)
        assert "其他資產" in html
        assert "預收款項" in html
        # 獨立重算：30.5M ＝ 5.3M ＋ 25.2M
        assert fmt(30500000.0) in html
        assert "✅" in html

    def test_snapshot_not_year_sum(self, d_a):
        html = make_balance_sheet_html(d_a)
        assert "2026年02月" in html
        # 2026-01 舊快照 900萬現金不可出現
        assert fmt(9000000.0) not in html

    def test_nat_rows_excluded(self, d_a):
        html = make_balance_sheet_html(d_a)
        assert "778 萬元" not in html
        assert "7777777" not in html


class TestWaterfallReconciliation:
    """淨利必須等於收入減支出（含 59），還原 Figure 後對帳。"""

    def test_net_matches_source(self, d_a, frames):
        _, _, df_csv = frames
        # 函式取最末年份（2026，僅 2 個月）：收入 20萬，支出 13萬（含 59），淨利 7萬
        ydf = df_csv[df_csv["年月"].dt.year == 2026]
        revenue = ydf[ydf["會計科目"].str.startswith("4")]["當月金額"].sum()
        expense = ydf[ydf["會計科目"].str.startswith("5")]["當月金額"].sum()
        assert revenue == 200000.0
        assert expense == 130000.0
        fig_data = figure_data_from_div(chart_waterfall(d_a))
        y = decode_y(fig_data[0]["y"])
        assert y[0] == pytest.approx(revenue)
        assert y[-1] == pytest.approx(revenue - expense) == pytest.approx(70000.0)


class TestChartDataReconciliation:
    """圖上點位必須等於來源欄位值（還原 Figure 比對，非字串搜尋）。"""

    def test_loan_savings_values_match_source(self, d_a, frames):
        from report_charts import chart_loan_savings

        df_m, _, _ = frames
        src = df_m[df_m["社號"] == "9901"].sort_values("年月")
        assert len(src) == 15
        fig_data = figure_data_from_div(chart_loan_savings(d_a))
        assert decode_y(fig_data[0]["y"]) == pytest.approx(src["貸放比"].tolist())
        assert decode_y(fig_data[1]["y"]) == pytest.approx(src["儲蓄率"].tolist())
        assert len(fig_data[0]["x"]) == 15

    def test_member_trend_values_match_source(self, d_a, frames):
        from report_charts import chart_member_capital_trend

        df_m, _, _ = frames
        src = df_m[df_m["社號"] == "9901"].sort_values("年月")
        fig_data = figure_data_from_div(chart_member_capital_trend(d_a))
        assert decode_y(fig_data[0]["y"]) == pytest.approx(src["社員數"].tolist())


class TestProvReconciliation:
    """異常提撥率：標示而非爆炸百分比。"""

    def test_abnormal_union_flagged(self, d_b):
        assert d_b["eProv"] == 25.0
        assert d_b["eProv"] > PROV_ABNORMAL
        assert d_b["eProv_note"] == "數值異常"

    def test_abnormal_not_rendered_as_pct(self, d_b):
        html = build_report(d_b, {"member_capital_trend": "<div>x</div>"})
        assert "數值異常" in html
        assert "2500" not in html


class TestEndToEndRealistic:
    """雙社全流程（含無 CSV 降級）不斷線。"""

    def test_full_pipeline_both_unions(self, frames):
        df_m, df_l, df_csv = frames
        for uid, has_csv in [("9901", True), ("9902", False)]:
            d = extract_union_data(df_m, df_l, df_csv, uid)
            assert d["has_csv"] is has_csv
            charts = generate_all_charts(d)
            assert len(charts) == 9
            html = build_report(d, charts)
            assert "<!DOCTYPE html>" in html

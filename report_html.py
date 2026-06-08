"""
HTML 模板組裝（使用 Jinja2 模板引擎）
"""
from html import escape as html_escape
from datetime import date
from jinja2 import Environment, FileSystemLoader
from report_config import THEME_BG, C, THRESHOLDS, fmt, fmt_pct, GEMINI_MODEL
from report_data import compute_ovd_stats

PLOTLY_JS_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"

_env = Environment(loader=FileSystemLoader("templates"))
_template = _env.get_template("report.html")


def df_to_html_table(df):
    rows = ""
    for _, r in df.iterrows():
        cells = "".join(f"<td>{v}</td>" for v in r)
        rows += f"<tr>{cells}</tr>"
    headers = "".join(f"<th>{c}</th>" for c in df.columns)
    return f"""<table class="data-table">
      <thead><tr>{headers}</tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


def build_report(d, charts, ai_analysis=None):
    """組裝完整 HTML 報告字串"""
    s_name = d["s_name"]
    s_no = d["s_no"]
    max_d = d["max_d"]
    status = d["status"]
    status_color = d["status_color"]
    reason_text = d["reason_text"]
    notes = d["notes"]
    data_end = max_d.strftime("%Y 年 %m 月")
    report_date = date.today().strftime("%Y 年 %m 月 %d 日")

    # KPI 卡片（社員→股金→貸放比→儲蓄率→逾放比→開支比→提撥率→診斷結果）
    kpi_cards = [
        {"label": "現有社員", "value": f"{int(d['curr_M']):,} 人",
         "sub": f"12M {'↑' if d['memG_curr'] >= 0 else '↓'} {abs(int(d['curr_M'] - d['M0'])):,} 人 ({fmt_pct(d['memG_curr'])})",
         "good": d['memG_curr'] >= 0},
        {"label": "現有股金", "value": fmt(d['curr_S']),
         "sub": f"12M {'↑' if d['shrG_curr'] >= 0 else '↓'} {fmt(abs(d['curr_S'] - d['S0']))} ({fmt_pct(d['shrG_curr'])})",
         "good": d['shrG_curr'] >= 0},
        {"label": "貸放比",  "value": fmt_pct(d['eLoan']),
         "sub": f"{'偏低' if d['eLoan'] < 0.4 else '偏高' if d['eLoan'] > 0.8 else '正常範圍'} (40–80%)",
         "good": 0.4 <= d['eLoan'] <= 0.8},
        {"label": "儲蓄率",  "value": fmt_pct(d['eRate']),
         "sub": "存款 / 股金", "good": d['eRate'] >= THRESHOLDS["savings_good"]},
        {"label": "逾放比",  "value": fmt_pct(d['eOvd']),
         "sub": f"{'警戒' if d['eOvd'] > 0.02 else '正常'} (警戒值 2%)",
         "good": d['eOvd'] <= 0.02},
        {"label": "開支比(年)", "value": fmt_pct(d['R0']),
         "sub": f"{'虧損' if d['R0'] > 1.0 else '盈餘'} (損益平衡 100%)",
         "good": d['R0'] <= 1.0},
        {"label": "提撥率",  "value": fmt_pct(d['eProv']),
         "sub": "備抵呆帳 / 逾期貸款", "good": d['eProv'] >= THRESHOLDS["provision_good"]},
        {"label": "診斷結果", "value": status,
         "sub": reason_text, "good": status.startswith("✅")},
    ]

    def kpi_card_html(card):
        color = C["green"] if card["good"] else C["red"]
        border = f"border-left: 5px solid {color};"
        return f"""<div class="kpi-card" style="{border}">
          <div class="kpi-label">{card['label']}</div>
          <div class="kpi-value" style="color:{color}">{card['value']}</div>
          <div class="kpi-sub">{card['sub']}</div>
        </div>"""

    kpi_html = "".join(kpi_card_html(c) for c in kpi_cards)

    # 逾放比統計摘要卡片
    ovd = compute_ovd_stats(d)
    ovd_stat_cards = [
        {"label": "最新逾放比",  "value": fmt_pct(ovd["curr"]),
         "sub": "最新一期數值", "good": ovd["curr"] <= THRESHOLDS["ovd_safe_line"]},
        {"label": "近 12M 平均", "value": fmt_pct(ovd["avg12"]),
         "sub": "過去 12 期平均", "good": ovd["avg12"] <= THRESHOLDS["ovd_safe_line"]},
        {"label": "歷史最高",    "value": fmt_pct(ovd["hist_max"]),
         "sub": f"發生於 {ovd['hist_max_d']}", "good": False},
        {"label": "歷史最低",    "value": fmt_pct(ovd["hist_min"]),
         "sub": f"發生於 {ovd['hist_min_d']}", "good": True},
        {"label": "超標月數",
         "value": f"{ovd['months_warn']} / {ovd['months_total']} M",
         "sub": "超過 2% 警戒線的月份數", "good": ovd["months_warn"] == 0},
        {"label": "近 6M 走勢",  "value": ovd["trend"],
         "sub": "以近 6M 首末值判定", "good": ovd["trend"] == "持續改善",
         "custom_color": ovd["trend_color"]},
        {"label": "最新提撥率",  "value": fmt_pct(ovd["prov_curr"]),
         "sub": "備抵呆帳 / 逾期貸款", "good": ovd["prov_curr"] >= ovd["curr"]},
    ]

    def ovd_stat_card_html(card):
        color = card.get("custom_color") or (C["green"] if card["good"] else C["red"])
        return f"""<div class="kpi-card" style="border-left:5px solid {color}">
          <div class="kpi-label">{card['label']}</div>
          <div class="kpi-value" style="color:{color}">{card['value']}</div>
          <div class="kpi-sub">{card['sub']}</div>
        </div>"""

    ovd_stats_html = "".join(ovd_stat_card_html(c) for c in ovd_stat_cards)

    # 近期資料表
    recent_m = d["df_m"].tail(12)[["年月", "社員數", "股金", "貸放比", "儲蓄率"]].copy()
    recent_m["年月"] = recent_m["年月"].dt.strftime("%Y-%m")
    recent_m["股金"] = recent_m["股金"].apply(fmt)
    recent_m["貸放比"] = recent_m["貸放比"].apply(fmt_pct)
    recent_m["儲蓄率"] = recent_m["儲蓄率"].apply(fmt_pct)
    recent_m["社員數"] = recent_m["社員數"].apply(lambda x: f"{int(x):,}")

    recent_l = d["df_l"].tail(12)[["年月", "逾放比", "開支比", "提撥率", "逾期貸款"]].copy()
    recent_l["年月"] = recent_l["年月"].dt.strftime("%Y-%m")
    recent_l["逾放比"] = recent_l["逾放比"].apply(fmt_pct)
    recent_l["開支比"] = recent_l["開支比"].apply(fmt_pct)
    recent_l["提撥率"] = recent_l["提撥率"].apply(fmt_pct)
    recent_l["逾期貸款"] = recent_l["逾期貸款"].apply(fmt)

    table_m_html = df_to_html_table(recent_m)
    table_l_html = df_to_html_table(recent_l)

    # 風險觸發項目
    if notes:
        note_spans = "".join(
            f'<span style="color:{C["red"]};font-weight:700">✗ {n}</span>&nbsp;&nbsp;'
            for n in notes
        )
    else:
        note_spans = '<span style="color:#10B981;font-weight:700">✓ 無警示項目</span>'

    # AI 顧問分析區塊
    ai_section = ""
    if ai_analysis:
        escaped = html_escape(ai_analysis)
        ai_section = f"""<div class="ai-box">
    <h3>🤖 儲互社 AI 顧問分析</h3>
    <p style="line-height:1.8;color:#475569;white-space:pre-wrap">{escaped}</p>
    <small style="color:#94A3B8;font-size:0.8rem">由 {GEMINI_MODEL} 產製，僅供參考</small>
  </div>"""

    ctx = dict(
        PLOTLY_JS_CDN=PLOTLY_JS_CDN,
        THEME_BG=THEME_BG,
        C=C,
        s_name=s_name,
        s_no=s_no,
        data_end=data_end,
        report_date=report_date,
        status=status,
        status_color=status_color,
        reason_text=reason_text,
        note_spans=note_spans,
        ai_section=ai_section,
        kpi_html=kpi_html,
        ovd_stats_html=ovd_stats_html,
        charts=charts,
        table_m_html=table_m_html,
        table_l_html=table_l_html,
    )
    return _template.render(ctx)

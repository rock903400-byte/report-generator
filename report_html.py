"""
HTML 模板組裝（使用 Jinja2 模板引擎）
"""
import re
from html import escape as html_escape
from datetime import date
from jinja2 import Environment, FileSystemLoader
from report_config import THEME_BG, C, THRESHOLDS, fmt, fmt_pct, GEMINI_MODEL
from report_data import compute_ovd_stats


def _inline_md(text):
    """行內 markdown → HTML（粗體、斜體）"""
    line_html = html_escape(text)
    line_html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line_html)
    line_html = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", line_html)
    return line_html


def _md_to_html(text):
    """簡易 markdown → HTML（處理 Gemini 常用格式）"""
    if not text or not text.strip():
        return ""

    lines = text.split("\n")
    out = []
    in_ul = False
    in_ol = False
    para_lines = []

    def _flush_para():
        if para_lines:
            p_content = " ".join(para_lines)
            out.append(f"<p>{_inline_md(p_content)}</p>")
            para_lines.clear()

    for line in lines:
        stripped = line.strip()

        # 標題
        m = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if m:
            _flush_para()
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if in_ol:
                out.append("</ol>")
                in_ol = False
            level = len(m.group(1)) + 2
            out.append(f"<h{level}>{_inline_md(m.group(2))}</h{level}>")
            continue

        # 無序列表
        if stripped.startswith("- ") or stripped.startswith("* "):
            _flush_para()
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{_inline_md(stripped[2:])}</li>")
            continue

        # 有序列表
        m = re.match(r"^\d+\.\s+(.+)$", stripped)
        if m:
            _flush_para()
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{_inline_md(m.group(1))}</li>")
            continue

        # 結束列表
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

        # 空行
        if not stripped:
            _flush_para()
            continue

        # 一般段落行
        para_lines.append(stripped)

    if in_ul:
        out.append("</ul>")
    if in_ol:
        out.append("</ol>")
    _flush_para()

    return "".join(out)


def _is_ai_truncated(text):
    """檢查 Gemini 回應是否被技術性截斷（未閉合的 markdown）"""
    if not text or not text.strip():
        return True
    text = text.strip()
    # 以未閉合 markdown 或截斷訊號結尾（"："表示清單項目沒有值，是 API token 截斷）
    if text.endswith("**") or text.endswith("*") or text.endswith("-") or text.endswith("："):
        return True
    return False

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
    ]

    def kpi_card_html(card):
        color = C["green"] if card["good"] else C["red"]
        return f"""<div class="kpi-card" style="--card-color:{color}">
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
    ]

    def ovd_stat_card_html(card):
        color = card.get("custom_color") or (C["green"] if card["good"] else C["red"])
        return f"""<div class="kpi-card" style="--card-color:{color}">
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
        if _is_ai_truncated(ai_analysis):
            ai_section = f"""<div class="ai-box">
    <h3>儲互社 AI 顧問分析</h3>
    <div style="line-height:1.65;color:#475569">
      <p>⚠️ AI 分析回應似乎被截斷或不完整，請重新產生報告或略過此分析。</p>
      <p style="color:#94A3B8;font-size:0.85rem;margin-top:0.5rem">原始回應片段：{html_escape(ai_analysis[:120])}…</p>
    </div>
    <div style="margin-top:0.8rem;padding-top:0.6rem;border-top:1px solid #DBEAFE">
      <small style="color:#94A3B8;font-size:0.78rem">由 {GEMINI_MODEL} 產製，僅供參考</small>
    </div>
  </div>"""
        else:
            ai_html = _md_to_html(ai_analysis)
            ai_section = f"""<div class="ai-box">
    <h3>儲互社 AI 顧問分析</h3>
    <div style="line-height:1.65;color:#475569">{ai_html}</div>
    <div style="margin-top:0.8rem;padding-top:0.6rem;border-top:1px solid #DBEAFE">
      <small style="color:#94A3B8;font-size:0.78rem">由 {GEMINI_MODEL} 產製，僅供參考</small>
    </div>
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

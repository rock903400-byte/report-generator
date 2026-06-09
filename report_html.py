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


def build_kpi_yoy_table(d):
    """KPI 年度對比表（所有可用年底快照，顏色標示好轉/惡化）"""
    df_m = d["df_m"]
    df_l = d["df_l"]

    m_ye = df_m[df_m["年月"].dt.month == 12].copy()
    l_ye = df_l[df_l["年月"].dt.month == 12].copy()

    all_years = sorted(
        set(list(m_ye["年月"].dt.year.unique()) + list(l_ye["年月"].dt.year.unique()))
    )
    if len(all_years) < 2:
        return "<p style='color:#94A3B8;padding:1rem'>年度資料不足（需至少 2 年）</p>"

    def _mval(yr, col):
        r = m_ye[m_ye["年月"].dt.year == yr]
        return float(r.iloc[-1][col]) if not r.empty and col in r.columns else None

    def _lval(yr, col):
        r = l_ye[l_ye["年月"].dt.year == yr]
        return float(r.iloc[-1][col]) if not r.empty and col in r.columns else None

    # 計算放款利率（410x 年利息 / 131x 月均淨額）
    lr = {}
    if d.get("has_csv") and not d["df_csv"].empty:
        dfc = d["df_csv"].copy()
        dfc["年"] = dfc["年月"].dt.year
        ii = (
            dfc[dfc["會計科目"].str.startswith("410")]
            .groupby(["年", "年月"])["當月金額"]
            .sum()
            .groupby(level=0)
            .sum()
        )
        lb = (
            dfc[dfc["會計科目"].str.startswith("131")]
            .groupby(["年", "年月"])["當月金額"]
            .sum()
            .groupby(level=0)
            .mean()
        )
        rs = (ii / lb * 100).dropna()
        cur_yr = int(dfc["年月"].dt.year.max())
        if dfc[dfc["年"] == cur_yr]["年月"].dt.month.nunique() < 10:
            rs = rs.drop(cur_yr, errors="ignore")
        lr = rs.to_dict()

    def _fmt_prov(yr):
        prov_v = _lval(yr, "提撥率")
        ovd_v = _lval(yr, "逾放比")
        if prov_v is None:
            return None
        if prov_v == 0 and ovd_v == 0:
            return "0.0%（無逾期）"
        if prov_v == 0 and ovd_v is not None and ovd_v > 0:
            r = l_ye[l_ye["年月"].dt.year == yr]
            is_missing = (
                bool(r.iloc[-1]["提撥率_缺失"])
                if not r.empty and "提撥率_缺失" in r.columns
                else True
            )
            if is_missing:
                return "—（資料缺失）"
        return fmt_pct(prov_v)

    prov_vals = {yr: _fmt_prov(yr) for yr in all_years}

    rows_def = [
        ("社員數", {yr: _mval(yr, "社員數") for yr in all_years}, lambda v: f"{int(v):,}人", "up"),
        ("股金", {yr: _mval(yr, "股金") for yr in all_years}, fmt, "up"),
        ("貸放比", {yr: _mval(yr, "貸放比") for yr in all_years}, fmt_pct, "range"),
        ("逾放比", {yr: _lval(yr, "逾放比") for yr in all_years}, fmt_pct, "down"),
        ("開支比", {yr: _lval(yr, "開支比") for yr in all_years}, fmt_pct, "down"),
        ("提撥率", prov_vals, lambda v: v if isinstance(v, str) else fmt_pct(v), "up"),
    ]
    if lr:
        rows_def.append(
            ("放款利率*", {yr: lr.get(yr) for yr in all_years}, lambda v: f"{v:.2f}%", "neutral")
        )

    def _bg(direction, curr, prev):
        if curr is None or prev is None:
            return ""
        if not isinstance(curr, (int, float)) or not isinstance(prev, (int, float)):
            return ""
        if direction == "up":
            return "#D1FAE5" if curr > prev * 1.001 else ("#FEE2E2" if curr < prev * 0.999 else "")
        if direction == "down":
            return "#D1FAE5" if curr < prev * 0.999 else ("#FEE2E2" if curr > prev * 1.001 else "")
        if direction == "range":
            in_c, in_p = 0.4 <= curr <= 0.8, 0.4 <= prev <= 0.8
            if in_c and not in_p:
                return "#D1FAE5"
            if not in_c and in_p:
                return "#FEE2E2"
        return ""

    def roc(yr):
        return f"民{yr - 1911}年底"

    th = "".join(f'<th style="text-align:center">{roc(yr)}</th>' for yr in all_years)
    body = ""
    for label, vals, fmt_fn, direction in rows_def:
        tds = []
        for i, yr in enumerate(all_years):
            v = vals.get(yr)
            txt = fmt_fn(v) if v is not None else "—"
            bg = _bg(direction, v, vals.get(all_years[i - 1])) if i > 0 else ""
            st = (
                f' style="background:{bg};text-align:center"'
                if bg
                else ' style="text-align:center"'
            )
            tds.append(f"<td{st}>{txt}</td>")
        body += (
            f'<tr><th style="text-align:left;white-space:nowrap">{label}</th>{"".join(tds)}</tr>\n'
        )

    note = (
        (
            '<p style="font-size:0.8rem;color:#94A3B8;padding:0.5rem 1rem">'
            "* 放款利率＝年度利息收入 / 平均放款餘額，月份不足 10 個月之年度不計入</p>"
        )
        if lr
        else ""
    )

    return (
        f'<table class="data-table" style="width:100%">'
        f'<thead><tr><th style="text-align:left">指標</th>{th}</tr></thead>'
        f"<tbody>{body}</tbody></table>{note}"
    )


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

    # ── 貸放比 / 儲蓄率 YoY 計算（對照前一年底） ──
    df_m_data = d["df_m"]
    T1 = d["T1"]
    _m1 = df_m_data[df_m_data["年月"] <= T1].sort_values("年月")
    loan_prev = float(_m1["貸放比"].iloc[-1]) if not _m1.empty else None


    if loan_prev is not None:
        _ld = d["eLoan"] - loan_prev
        loan_yoy = f"  {'▲' if _ld >= 0 else '▼'} {abs(_ld * 100):.1f}pp vs 去年"
    else:
        loan_yoy = ""

    sav_thr = THRESHOLDS["savings_good"]
    prov_thr = THRESHOLDS["provision_good"]
    sav_ok = d["eRate"] >= sav_thr
    prov_ok = d["eProv"] >= prov_thr

    prov_note = d.get("eProv_note", "")
    if prov_note == "資料缺失":
        prov_value = "—（資料缺失）"
        prov_sub = "原始資料缺漏"
        prov_good = True
    elif prov_note == "無逾期":
        prov_value = "0.0%（無逾期）"
        prov_sub = "無逾期貸款，無需提撥"
        prov_good = True
    else:
        prov_value = fmt_pct(d["eProv"])
        prov_sub = f"{'充足 ✓' if prov_ok else '不足 ✗'}（門檻 {prov_thr * 100:.0f}%）"
        prov_good = prov_ok

    # ── KPI 卡片（風險觸發數排第一） ──
    rc = d.get("risk_count", 0)
    kpi_cards = [
        {
            "label": "風險觸發數",
            "value": f"{rc} / 5 條件",
            "sub": d["status"],
            "good": rc == 0,
            "custom_color": d["status_color"],
        },
        {
            "label": "現有社員",
            "value": f"{int(d['curr_M']):,} 人",
            "sub": f"12M {'↑' if d['memG_curr'] >= 0 else '↓'} {abs(int(d['curr_M'] - d['M0'])):,} 人 ({fmt_pct(d['memG_curr'])})",
            "good": d["memG_curr"] >= 0,
        },
        {
            "label": "現有股金",
            "value": fmt(d["curr_S"]),
            "sub": f"12M {'↑' if d['shrG_curr'] >= 0 else '↓'} {fmt(abs(d['curr_S'] - d['S0']))} ({fmt_pct(d['shrG_curr'])})",
            "good": d["shrG_curr"] >= 0,
        },
        {
            "label": "貸放比",
            "value": fmt_pct(d["eLoan"]),
            "sub": f"{'偏低' if d['eLoan'] < 0.4 else '偏高' if d['eLoan'] > 0.8 else '正常範圍'} (40–80%){loan_yoy}",
            "good": 0.4 <= d["eLoan"] <= 0.8,
        },
        {
            "label": "儲蓄率",
            "value": fmt_pct(d["eRate"]),
            "sub": f"門檻 {sav_thr * 100:.0f}%，{'達標 ✓' if sav_ok else '未達標 ✗'}",
            "good": sav_ok,
        },
        {
            "label": "逾放比",
            "value": fmt_pct(d["eOvd"]),
            "sub": f"{'⚠ 警戒' if d['eOvd'] > 0.02 else '✓ 正常'} (警戒值 2%)",
            "good": d["eOvd"] <= 0.02,
        },
        {
            "label": "開支比(年)",
            "value": fmt_pct(d["R0"]),
            "sub": f"{'⚠ 虧損' if d['R0'] > 1.0 else '✓ 盈餘'} (損益平衡 100%)",
            "good": d["R0"] <= 1.0,
        },
        {"label": "提撥率", "value": prov_value, "sub": prov_sub, "good": prov_good},
    ]

    def kpi_card_html(card):
        color = card.get("custom_color") or (C["green"] if card["good"] else C["red"])
        return f"""<div class="kpi-card" style="--card-color:{color}">
          <div class="kpi-label">{card['label']}</div>
          <div class="kpi-value" style="color:{color}">{card['value']}</div>
          <div class="kpi-sub">{card['sub']}</div>
        </div>"""

    kpi_html = "".join(kpi_card_html(c) for c in kpi_cards)

    # 逾放比統計摘要卡片
    ovd = compute_ovd_stats(d)
    ovd_stat_cards = [
        {
            "label": "最新逾放比",
            "value": fmt_pct(ovd["curr"]),
            "sub": "最新一期數值",
            "good": ovd["curr"] <= THRESHOLDS["ovd_safe_line"],
        },
        {
            "label": "近 12M 平均",
            "value": fmt_pct(ovd["avg12"]),
            "sub": "過去 12 期平均",
            "good": ovd["avg12"] <= THRESHOLDS["ovd_safe_line"],
        },
        {
            "label": "歷史最高",
            "value": fmt_pct(ovd["hist_max"]),
            "sub": f"發生於 {ovd['hist_max_d']}",
            "good": False,
        },
        {
            "label": "歷史最低",
            "value": fmt_pct(ovd["hist_min"]),
            "sub": f"發生於 {ovd['hist_min_d']}",
            "good": True,
        },
        {
            "label": "超標月數",
            "value": f"{ovd['months_warn']} / {ovd['months_total']} M",
            "sub": "超過 2% 警戒線的月份數",
            "good": ovd["months_warn"] == 0,
        },
        {
            "label": "近 6M 走勢",
            "value": ovd["trend"],
            "sub": "以近 6M 首末值判定",
            "good": ovd["trend"] == "持續改善",
            "custom_color": ovd["trend_color"],
        },
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

    def _fmt_prov_row(row):
        prov = row["提撥率"]
        ovd = row["逾放比"]
        if prov == 0 and ovd == 0:
            return "0.0%（無逾期）"
        if prov == 0 and ovd > 0:
            is_missing = row.get("提撥率_缺失", True)
            if is_missing:
                return "—（資料缺失）"
        return fmt_pct(prov)

    recent_l["提撥率"] = recent_l.apply(_fmt_prov_row, axis=1)
    recent_l["逾放比"] = recent_l["逾放比"].apply(fmt_pct)
    recent_l["開支比"] = recent_l["開支比"].apply(fmt_pct)
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

    kpi_yoy_html = build_kpi_yoy_table(d)

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
        kpi_yoy_html=kpi_yoy_html,
        ovd_stats_html=ovd_stats_html,
        charts=charts,
        table_m_html=table_m_html,
        table_l_html=table_l_html,
    )
    return _template.render(ctx)

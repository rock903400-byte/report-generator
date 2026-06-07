"""
HTML 模板組裝（沿用達邦報告 layout）
"""
from datetime import date
from report_config import THEME_BG, C, THRESHOLDS, fmt, fmt_pct

PLOTLY_JS_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"

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

def build_report(d, charts):
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

    # KPI 卡片
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
         "sub": "存款 / 股金", "good": d['eRate'] >= 0.6},
        {"label": "逾放比",  "value": fmt_pct(d['eOvd']),
         "sub": f"{'警戒' if d['eOvd'] > 0.02 else '正常'} (警戒值 2%)",
         "good": d['eOvd'] <= 0.02},
        {"label": "開支比(年)", "value": fmt_pct(d['R0']),
         "sub": f"{'虧損' if d['R0'] > 1.0 else '盈餘'} (損益平衡 100%)",
         "good": d['R0'] <= 1.0},
        {"label": "提撥率",  "value": fmt_pct(d['eProv']),
         "sub": "備抵呆帳 / 逾期貸款", "good": d['eProv'] >= 0.01},
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
    from report_data import compute_ovd_stats
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

    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{s_name} 財務分析報告</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;600;700;900&display=swap" rel="stylesheet">
  <script src="{PLOTLY_JS_CDN}"></script>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Noto Sans TC', sans-serif;
      background: {THEME_BG};
      color: #1E293B;
      font-size: 16px;
      line-height: 1.6;
    }}
    .report-header {{
      background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
      color: #fff;
      padding: 2.5rem 3rem;
    }}
    .report-header h1 {{
      font-size: 2.2rem;
      font-weight: 900;
      letter-spacing: 0.02em;
      margin-bottom: 0.5rem;
    }}
    .report-header .meta {{
      font-size: 1rem;
      color: #94A3B8;
    }}
    .status-badge {{
      display: inline-block;
      background: {status_color};
      color: #fff;
      font-size: 1.1rem;
      font-weight: 700;
      padding: 6px 18px;
      border-radius: 100px;
      margin-top: 0.8rem;
    }}
    .container {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 2rem 1.5rem;
    }}
    .section-title {{
      font-size: 1.5rem;
      font-weight: 700;
      color: #1E293B;
      padding: 0.5rem 0 1rem;
      border-bottom: 3px solid {C["blue"]};
      margin-bottom: 1.5rem;
    }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
      gap: 1rem;
      margin-bottom: 2.5rem;
    }}
    .kpi-card {{
      background: #fff;
      border-radius: 14px;
      padding: 1.2rem 1.4rem;
      box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }}
    .kpi-label {{
      font-size: 0.95rem;
      font-weight: 600;
      color: #64748B;
      margin-bottom: 0.4rem;
    }}
    .kpi-value {{
      font-size: 1.8rem;
      font-weight: 900;
      line-height: 1.2;
      word-break: break-all;
    }}
    .kpi-sub {{
      font-size: 0.85rem;
      color: #94A3B8;
      margin-top: 0.3rem;
    }}
    .chart-grid-2 {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5rem;
      margin-bottom: 2rem;
    }}
    .chart-full {{
      margin-bottom: 2rem;
    }}
    .chart-box {{
      background: #fff;
      border-radius: 14px;
      padding: 1rem;
      box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }}
    .data-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.95rem;
    }}
    .data-table th {{
      background: #1E293B;
      color: #fff;
      padding: 10px 12px;
      text-align: center;
      font-weight: 600;
    }}
    .data-table td {{
      padding: 9px 12px;
      text-align: center;
      border-bottom: 1px solid #E2E8F0;
    }}
    .data-table tr:nth-child(even) td {{
      background: #F8FAFC;
    }}
    .risk-box {{
      background: #fff;
      border-radius: 14px;
      border-left: 6px solid {status_color};
      padding: 1.2rem 1.5rem;
      margin-bottom: 2rem;
      box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }}
    .risk-box h3 {{
      font-size: 1.3rem;
      font-weight: 700;
      color: {status_color};
      margin-bottom: 0.6rem;
    }}
    .risk-box p {{
      color: #475569;
      line-height: 1.8;
    }}
    .report-footer {{
      text-align: center;
      padding: 2rem;
      color: #94A3B8;
      font-size: 0.9rem;
      border-top: 1px solid #E2E8F0;
      margin-top: 2rem;
    }}
    @media (max-width: 768px) {{
      .chart-grid-2 {{ grid-template-columns: 1fr; }}
      .report-header {{ padding: 1.5rem; }}
      .report-header h1 {{ font-size: 1.6rem; }}
      .kpi-value {{ font-size: 1.5rem; }}
    }}
  </style>
</head>
<body>

<div class="report-header">
  <h1>📊 {s_name} 財務分析報告</h1>
  <div class="meta">社號：{s_no}　｜　資料截至：{data_end}　｜　報告產製：{report_date}</div>
  <div class="status-badge">{status}</div>
</div>

<div class="container">

  <h2 class="section-title">🔍 風險診斷摘要</h2>
  <div class="risk-box">
    <h3>{status}</h3>
    <p>
      <strong>觸發事項：</strong>{reason_text}<br>
      風險診斷採「2/5 原則」，滿足以下任兩項即列為重點輔導：
      連兩年虧損（開支比&gt;100%）、貸放比偏低（&lt;10%）、逾放比偏高且惡化、社員連三年衰退、股金連三年衰退。<br>
      <br>
      本次診斷觸發項目：
      {note_spans}
    </p>
  </div>

  <h2 class="section-title">📌 關鍵指標一覽</h2>
  <div class="kpi-grid">
    {kpi_html}
  </div>

  <h2 class="section-title">👥 社員數 & 股金趨勢</h2>
  <div class="chart-grid-2">
    <div class="chart-box">{charts['member_trend']}</div>
    <div class="chart-box">{charts['capital_trend']}</div>
  </div>

  <h2 class="section-title">📉 資金運用 & 風險指標趨勢</h2>
  <div class="chart-grid-2">
    <div class="chart-box">{charts['loan_savings']}</div>
    <div class="chart-box">{charts['risk_trend']}</div>
  </div>

  <h2 class="section-title">🔬 逾放比深度分析</h2>
  <div class="kpi-grid" style="margin-bottom:1.5rem">{ovd_stats_html}</div>
  <div class="chart-full chart-box" style="margin-bottom:1.5rem">{charts['ovd_full_history']}</div>
  <div class="chart-full chart-box" style="margin-bottom:2rem">{charts['ovd_amount']}</div>

  <h2 class="section-title">💰 財務科目分析</h2>
  <div class="chart-full chart-box">{charts['balance_sheet']}</div>
  <div class="chart-full chart-box" style="margin-top:1.5rem">{charts['annual_trend']}</div>
  <div class="chart-full chart-box" style="margin-top:1.5rem">{charts['waterfall']}</div>

  <h2 class="section-title">📋 近 12 期社務資料</h2>
  <div class="chart-box" style="overflow-x:auto;margin-bottom:2rem">{table_m_html}</div>

  <h2 class="section-title">📋 近 12 期放款資料</h2>
  <div class="chart-box" style="overflow-x:auto;margin-bottom:2rem">{table_l_html}</div>

</div>

<div class="report-footer">
  本報告由穿透系統自動產製 ｜ {report_date}<br>
  資料來源：{s_name}（社號 {s_no}）
</div>

</body>
</html>"""
    return html

"""
Plotly 圖表產生（參數化，與社別脫鉤）
"""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from report_config import THRESHOLDS, THEME_BG, C, PLOTLY_CFG, fmt, fmt_pct, safe_div

def style_fig(fig, title="", height=500):
    fig.update_layout(
        title=dict(text=title, font=dict(size=22, color=C["text"]), x=0) if title else None,
        plot_bgcolor=THEME_BG,
        paper_bgcolor=THEME_BG,
        font=dict(size=15, color=C["text"]),
        margin=dict(l=10, r=10, t=55, b=40),
        height=height,
        dragmode=False,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    fig.update_xaxes(fixedrange=True, gridcolor="rgba(0,0,0,0.05)")
    fig.update_yaxes(fixedrange=True, gridcolor="rgba(0,0,0,0.05)")
    return fig

def to_html_div(fig):
    return fig.to_html(full_html=False, include_plotlyjs=False, config=PLOTLY_CFG)


def chart_member_capital_trend(d):
    df = d["df_m"][["年月", "社員數", "股金"]].copy()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=df["年月"], y=df["社員數"],
        name="社員數", marker_color=C["blue"], opacity=0.55,
        hovertemplate="%{x}<br>社員數：%{y:,} 人<extra></extra>",
        width=0.5,
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=df["年月"], y=df["社員數"].rolling(3, min_periods=1).mean(),
        name="社員數 3M 均線", mode="lines",
        line=dict(color=C["blue"], width=2.5),
        hovertemplate="%{x}<br>社員數 3M 均：%{y:,.0f} 人<extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Bar(
        x=df["年月"], y=df["股金"],
        name="股金", marker_color=C["green"], opacity=0.55,
        hovertemplate="%{x}<br>股金：%{y:,.0f}<extra></extra>",
        width=0.5,
    ), secondary_y=True)
    fig.add_trace(go.Scatter(
        x=df["年月"], y=df["股金"].rolling(3, min_periods=1).mean(),
        name="股金 3M 均線", mode="lines",
        line=dict(color=C["green"], width=2.5, dash="dot"),
        hovertemplate="%{x}<br>股金 3M 均：%{y:,.0f}<extra></extra>",
    ), secondary_y=True)

    last_m = df.iloc[-1]
    fig.add_annotation(
        x=last_m["年月"], y=last_m["社員數"],
        text=f'{int(last_m["社員數"]):,} 人',
        font=dict(size=13, color=C["blue"]),
        showarrow=True, arrowhead=0, ax=0, ay=-28,
        bgcolor="rgba(255,255,255,0.85)", bordercolor=C["blue"],
        borderpad=4, borderwidth=1,
    )
    fig.add_annotation(
        x=last_m["年月"], y=last_m["股金"],
        text=f'{last_m["股金"]/1e4:.0f} 萬',
        font=dict(size=13, color=C["green"]),
        showarrow=True, arrowhead=0, ax=0, ay=28,
        bgcolor="rgba(255,255,255,0.85)", bordercolor=C["green"],
        borderpad=4, borderwidth=1,
    )

    fig.update_layout(
        barmode="overlay",
        title=None,
        plot_bgcolor=THEME_BG, paper_bgcolor=THEME_BG,
        font=dict(size=15, color=C["text"]),
        margin=dict(l=10, r=10, t=20, b=40),
        height=400,
        dragmode=False, hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    fig.update_xaxes(fixedrange=True, gridcolor="rgba(0,0,0,0.05)")
    fig.update_yaxes(fixedrange=True, gridcolor="rgba(0,0,0,0.05)",
                     title_text="社員數（人）", secondary_y=False)
    fig.update_yaxes(fixedrange=True, gridcolor="rgba(0,0,0,0.05)",
                     tickformat=".2s", title_text="股金（元）", secondary_y=True)
    return to_html_div(fig)


def chart_loan_savings(d):
    df = d["df_m"][["年月", "貸放比", "儲蓄率"]].copy()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(
        x=df["年月"], y=df["貸放比"],
        name="貸放比", mode="lines+markers",
        line=dict(color=C["blue"], width=3),
        marker=dict(size=6),
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=df["年月"], y=df["儲蓄率"],
        name="儲蓄率", mode="lines+markers",
        line=dict(color=C["green"], width=3, dash="dot"),
        marker=dict(size=6),
    ), secondary_y=True)
    fig.add_hline(y=THRESHOLDS["stable_loan_min"], line_dash="dash",
                  line_color=C["red"], opacity=0.5, annotation_text="貸放比下限 40%")
    fig.add_hline(y=THRESHOLDS["stable_loan_max"], line_dash="dash",
                  line_color=C["amber"], opacity=0.5, annotation_text="貸放比上限 80%")
    fig.update_layout(
        title=None,
        plot_bgcolor=THEME_BG, paper_bgcolor=THEME_BG,
        font=dict(size=15, color=C["text"]), margin=dict(l=10, r=10, t=20, b=40),
        height=380, dragmode=False, hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    fig.update_xaxes(fixedrange=True, gridcolor="rgba(0,0,0,0.05)")
    fig.update_yaxes(fixedrange=True, gridcolor="rgba(0,0,0,0.05)", tickformat=".1%", secondary_y=False)
    fig.update_yaxes(fixedrange=True, gridcolor="rgba(0,0,0,0.05)", tickformat=".1%", secondary_y=True)
    return to_html_div(fig)


def chart_risk_trend(d):
    df_o = d["df_l"][["年月", "逾放比", "開支比"]].copy()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(
        x=df_o["年月"], y=df_o["逾放比"],
        name="逾放比", mode="lines+markers",
        line=dict(color=C["red"], width=3),
        marker=dict(size=6),
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=df_o["年月"], y=df_o["開支比"],
        name="開支比", mode="lines+markers",
        line=dict(color=C["indigo"], width=3, dash="dot"),
        marker=dict(size=6),
    ), secondary_y=True)
    fig.add_hline(y=THRESHOLDS["ovd_safe_line"], line_dash="dash",
                  line_color=C["amber"], opacity=0.6, annotation_text="逾放比警戒 2%")
    fig.add_hline(y=1.0, line_dash="dash", line_color=C["red"],
                  opacity=0.5, annotation_text="開支比損益平衡 100%", secondary_y=True)
    fig.update_layout(
        title=None,
        plot_bgcolor=THEME_BG, paper_bgcolor=THEME_BG,
        font=dict(size=15, color=C["text"]), margin=dict(l=10, r=10, t=20, b=40),
        height=380, dragmode=False, hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    fig.update_xaxes(fixedrange=True, gridcolor="rgba(0,0,0,0.05)")
    fig.update_yaxes(fixedrange=True, gridcolor="rgba(0,0,0,0.05)", tickformat=".2%", secondary_y=False)
    fig.update_yaxes(fixedrange=True, gridcolor="rgba(0,0,0,0.05)", tickformat=".1%", secondary_y=True)
    return to_html_div(fig)


def chart_ovd_full_history(d):
    df = d["df_l"][["年月", "逾放比"]].copy()
    WARN = THRESHOLDS["ovd_safe_line"]
    df["3M均"] = df["逾放比"].rolling(3, min_periods=1).mean()
    df["6M均"] = df["逾放比"].rolling(6, min_periods=1).mean()
    y_max = max(df["逾放比"].max() * 1.2, WARN * 3)

    fig = go.Figure()
    fig.add_hrect(
        y0=WARN, y1=y_max,
        fillcolor="rgba(239,68,68,0.07)", line_width=0,
        annotation_text="警戒區（逾放比 > 2%）",
        annotation_position="top left",
        annotation_font=dict(color=C["red"], size=12),
    )
    fig.add_trace(go.Scatter(
        x=df["年月"], y=df["逾放比"],
        name="逾放比（月）", mode="lines+markers",
        line=dict(color=C["red"], width=2.5),
        marker=dict(size=4),
    ))
    fig.add_trace(go.Scatter(
        x=df["年月"], y=df["3M均"],
        name="3M 均線", mode="lines",
        line=dict(color=C["amber"], width=2.5, dash="dot"),
    ))
    fig.add_trace(go.Scatter(
        x=df["年月"], y=df["6M均"],
        name="6M 均線", mode="lines",
        line=dict(color=C["blue"], width=2.5, dash="dash"),
    ))
    fig.add_hline(y=WARN, line_dash="dash", line_color=C["amber"],
                  line_width=2, annotation_text="警戒線 2%",
                  annotation_position="bottom right")

    peak_idx = df["逾放比"].idxmax()
    fig.add_trace(go.Scatter(
        x=[df.loc[peak_idx, "年月"]], y=[df.loc[peak_idx, "逾放比"]],
        mode="markers+text",
        marker=dict(color=C["red"], size=12, symbol="triangle-up"),
        text=[f"最高 {fmt_pct(df.loc[peak_idx, '逾放比'])}"],
        textposition="top center",
        textfont=dict(size=12, color=C["red"]),
        showlegend=False,
    ))
    low_idx = df["逾放比"].idxmin()
    fig.add_trace(go.Scatter(
        x=[df.loc[low_idx, "年月"]], y=[df.loc[low_idx, "逾放比"]],
        mode="markers+text",
        marker=dict(color=C["green"], size=12, symbol="triangle-down"),
        text=[f"最低 {fmt_pct(df.loc[low_idx, '逾放比'])}"],
        textposition="bottom center",
        textfont=dict(size=12, color=C["green"]),
        showlegend=False,
    ))

    style_fig(fig, height=440)
    fig.update_yaxes(tickformat=".2%", range=[0, y_max])
    return to_html_div(fig)


def chart_ovd_amount(d):
    df = d["df_l"][["年月", "逾期貸款", "逾放比"]].copy()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=df["年月"], y=df["逾期貸款"],
        name="逾期貸款金額",
        marker_color=C["red"], opacity=0.5,
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=df["年月"], y=df["逾放比"],
        name="逾放比",
        mode="lines+markers",
        line=dict(color=C["amber"], width=3),
        marker=dict(size=5),
    ), secondary_y=True)
    fig.add_hline(y=THRESHOLDS["ovd_safe_line"], line_dash="dash",
                  line_color=C["red"], opacity=0.6,
                  annotation_text="警戒線 2%", secondary_y=True)

    fig.update_layout(
        title=None,
        plot_bgcolor=THEME_BG, paper_bgcolor=THEME_BG,
        font=dict(size=15, color=C["text"]), margin=dict(l=10, r=10, t=20, b=40),
        height=400, dragmode=False, hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    fig.update_xaxes(fixedrange=True, gridcolor="rgba(0,0,0,0.05)")
    fig.update_yaxes(fixedrange=True, tickformat=".2s", title_text="逾期貸款（元）",
                     gridcolor="rgba(0,0,0,0.05)", secondary_y=False)
    fig.update_yaxes(fixedrange=True, tickformat=".2%", title_text="逾放比",
                     gridcolor="rgba(0,0,0,0.05)", secondary_y=True)
    return to_html_div(fig)


def chart_waterfall(d):
    if not d["has_csv"] or d["df_csv"].empty:
        return "<p style='color:#94A3B8'>無 CSV 財務資料</p>"

    df = d["df_csv"]
    years = sorted(df[df["年月"].notna()]["年月"].dt.year.unique())
    if not years:
        return "<p style='color:#94A3B8'>無年度資料</p>"
    yr = years[-1]

    yr_df = df[df["年月"].dt.year == yr].copy()
    revenue = yr_df[yr_df["會計科目"].str.startswith("4")]["當月金額"].sum()
    expense = yr_df[yr_df["會計科目"].str.startswith("5")]["當月金額"].sum()

    def grp(pfx):
        return yr_df[yr_df["會計科目"].str.startswith(pfx)]["當月金額"].sum()
    exp_groups = {}
    if grp("51") > 0: exp_groups["利息支出"] = grp("51")
    if grp("52") > 0: exp_groups["人事費用"] = grp("52")
    if grp("53") > 0: exp_groups["業務費用"] = grp("53")
    if grp("54") > 0: exp_groups["管理費用"] = grp("54")
    if grp("55") > 0: exp_groups["呆帳費用"] = grp("55")
    if grp("56") > 0: exp_groups["協會及捐贈費"] = grp("56")
    if grp("57") > 0: exp_groups["教育社務費"] = grp("57")
    if grp("58") > 0: exp_groups["獎勵費"] = grp("58")
    net = revenue - expense

    labels = ["總收入"] + list(exp_groups.keys()) + ["本期損益"]
    values = [revenue] + [-v for v in exp_groups.values()] + [net]
    measures = ["absolute"] + ["relative"] * len(exp_groups) + ["total"]
    colors = (
        [C["green"]]
        + [C["red"]] * len(exp_groups)
        + [C["green"] if net >= 0 else C["red"]]
    )

    fig = go.Figure(go.Waterfall(
        name="", orientation="v",
        measure=measures,
        x=labels, y=values,
        connector=dict(line=dict(color="rgba(0,0,0,0.2)", width=1)),
        increasing=dict(marker=dict(color=C["green"])),
        decreasing=dict(marker=dict(color=C["red"])),
        totals=dict(marker=dict(color=C["blue"])),
        text=[fmt(v) for v in values],
        textposition="outside",
        textfont=dict(size=13),
    ))
    style_fig(fig, height=480)
    fig.update_layout(showlegend=False)
    return to_html_div(fig)


def chart_annual_trend(d):
    if not d["has_csv"] or d["df_csv"].empty:
        return "<p style='color:#94A3B8'>無 CSV 財務資料</p>"

    df = d["df_csv"].copy()
    df["年度"] = df["年月"].dt.year
    agg = df.groupby(["年度", "會計科目"]).agg({"當月金額": "sum"}).reset_index()

    rev_by_yr = agg[agg["會計科目"].str.startswith("4")].groupby("年度")["當月金額"].sum().reset_index()
    rev_by_yr.columns = ["年度", "收入"]
    exp_by_yr = agg[agg["會計科目"].str.startswith("5")].groupby("年度")["當月金額"].sum().reset_index()
    exp_by_yr.columns = ["年度", "支出"]

    merged = rev_by_yr.merge(exp_by_yr, on="年度", how="outer").fillna(0)
    merged["損益"] = merged["收入"] - merged["支出"]
    merged["開支比"] = merged.apply(lambda r: safe_div(r["支出"], r["收入"]), axis=1)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=merged["年度"], y=merged["收入"], name="收入",
                         marker_color=C["green"], opacity=0.8), secondary_y=False)
    fig.add_trace(go.Bar(x=merged["年度"], y=merged["支出"], name="支出",
                         marker_color=C["red"], opacity=0.8), secondary_y=False)
    fig.add_trace(go.Scatter(x=merged["年度"], y=merged["開支比"],
                             name="開支比", mode="lines+markers",
                             line=dict(color=C["blue"], width=3),
                             marker=dict(size=8)), secondary_y=True)
    fig.add_hline(y=1.0, line_dash="dash", line_color=C["red"],
                  opacity=0.5, annotation_text="損益平衡", secondary_y=True)
    fig.update_layout(
        title=None,
        barmode="group", plot_bgcolor=THEME_BG, paper_bgcolor=THEME_BG,
        font=dict(size=15, color=C["text"]), margin=dict(l=10, r=10, t=20, b=40),
        height=380, dragmode=False, hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    fig.update_xaxes(fixedrange=True, gridcolor="rgba(0,0,0,0.05)", type="category")
    fig.update_yaxes(fixedrange=True, gridcolor="rgba(0,0,0,0.05)", tickformat=".2s", secondary_y=False)
    fig.update_yaxes(fixedrange=True, gridcolor="rgba(0,0,0,0.05)", tickformat=".1%", secondary_y=True)
    return to_html_div(fig)


def make_balance_sheet_html(d):
    if not d["has_csv"] or d["df_csv"].empty:
        return "<p style='color:#94A3B8'>無 CSV 財務資料</p>"

    df = d["df_csv"]
    latest_yr = int(df[df["年月"].notna()]["年月"].dt.year.max())
    yr_df = df[df["年月"].dt.year == latest_yr].copy()

    def accs(*pfxs):
        rows = []
        for p in pfxs:
            g = (yr_df[yr_df["會計科目"].str.startswith(p)]
                 .groupby(["會計科目", "會科名稱"])["當月金額"].sum()
                 .reset_index())
            g = g[g["當月金額"].abs() > 0].sort_values("會計科目")
            rows.extend(g.to_dict("records"))
        return rows

    def sub(rows):
        return sum(r["當月金額"] for r in rows)

    def row_html(name, amt, indent=True, bold=False, bg=""):
        pad = "padding-left:1.4rem;" if indent else ""
        fw = "font-weight:700;" if bold else ""
        bgcss = f"background:{bg};" if bg else ""
        color = "#EF4444" if amt < 0 else "#1E293B"
        return (f'<tr style="{bgcss}">'
                f'<td style="{pad}{fw}font-size:0.92rem;color:#475569">{name}</td>'
                f'<td style="text-align:right;{fw}font-size:0.92rem;color:{color}">{fmt(amt)}</td>'
                f'</tr>')

    def hdr(title):
        return (f'<tr style="background:#E2E8F0">'
                f'<td colspan="2" style="font-weight:700;font-size:0.95rem;'
                f'color:#1E293B;padding:8px 12px;letter-spacing:0.02em">{title}</td>'
                f'</tr>')

    def sub_row(label, total):
        clr = "#10B981" if total >= 0 else "#EF4444"
        return (f'<tr style="background:#F8FAFC;border-top:1.5px solid #CBD5E1">'
                f'<td style="font-weight:600;font-size:0.92rem;padding-left:0.8rem">{label}</td>'
                f'<td style="text-align:right;font-weight:700;color:{clr};font-size:0.92rem">{fmt(total)}</td>'
                f'</tr>')

    def total_row(label, total):
        clr = "#10B981" if total >= 0 else "#EF4444"
        return (f'<tr style="background:#1E293B">'
                f'<td style="color:#fff;font-weight:700;font-size:1rem">{label}</td>'
                f'<td style="text-align:right;font-weight:700;color:{clr};font-size:1rem">{fmt(total)}</td>'
                f'</tr>')

    cash = accs("11")
    invest = accs("12")
    loans = accs("13")
    guar = accs("14")
    fixed = accs("15")
    total_assets = sub(cash) + sub(invest) + sub(loans) + sub(guar) + sub(fixed)

    payab = accs("21")
    dep = accs("23")
    borrow = accs("25")
    othl = accs("27")
    total_liab = sub(payab) + sub(dep) + sub(borrow) + sub(othl)

    cap = accs("31")
    resv = accs("32")
    earn = accs("33")
    total_eq = sub(cap) + sub(resv) + sub(earn)

    asset_body = (
        hdr("現金、存款及應收款") +
        "".join(row_html(r["會科名稱"], r["當月金額"]) for r in cash) +
        sub_row("現金、存款及應收款 小計", sub(cash)) +
        hdr("預付費用") +
        "".join(row_html(r["會科名稱"], r["當月金額"]) for r in invest) +
        sub_row("預付費用 小計", sub(invest)) +
        hdr("放款") +
        "".join(row_html(r["會科名稱"], r["當月金額"]) for r in loans) +
        sub_row("放款 小計", sub(loans)) +
        hdr("存出保證金") +
        "".join(row_html(r["會科名稱"], r["當月金額"]) for r in guar) +
        sub_row("存出保證金 小計", sub(guar)) +
        hdr("固定資產") +
        "".join(row_html(r["會科名稱"], r["當月金額"]) for r in fixed) +
        sub_row("固定資產 小計", sub(fixed)) +
        total_row("資產合計", total_assets)
    )

    le_body = (
        hdr("【負債】應付費用") +
        "".join(row_html(r["會科名稱"], r["當月金額"]) for r in payab) +
        sub_row("應付費用 小計", sub(payab)) +
        hdr("【負債】吸收存款") +
        "".join(row_html(r["會科名稱"], r["當月金額"]) for r in dep) +
        sub_row("吸收存款 小計", sub(dep)) +
        hdr("【負債】遞延收入") +
        "".join(row_html(r["會科名稱"], r["當月金額"]) for r in borrow) +
        sub_row("遞延收入 小計", sub(borrow)) +
        hdr("【負債】其他負債") +
        "".join(row_html(r["會科名稱"], r["當月金額"]) for r in othl) +
        sub_row("其他負債 小計", sub(othl)) +
        total_row("負債合計", total_liab) +
        hdr("【權益】股金") +
        "".join(row_html(r["會科名稱"], r["當月金額"]) for r in cap) +
        sub_row("股金 小計", sub(cap)) +
        hdr("【權益】捐贈及補助公積") +
        "".join(row_html(r["會科名稱"], r["當月金額"]) for r in resv) +
        sub_row("捐贈及補助公積 小計", sub(resv)) +
        hdr("【權益】公積金及盈餘") +
        "".join(row_html(r["會科名稱"], r["當月金額"]) for r in earn) +
        sub_row("公積金及盈餘 小計", sub(earn)) +
        total_row("權益合計", total_eq) +
        total_row("負債及權益合計", total_liab + total_eq)
    )

    tbl_style = "width:100%;border-collapse:collapse;font-size:0.92rem;"
    th_style = ("background:#1E293B;color:#fff;padding:10px 12px;"
                "font-size:1rem;font-weight:700;text-align:left;")

    bal_ok = abs(total_assets - (total_liab + total_eq)) < 1
    bal_icon = "✅" if bal_ok else "⚠️"
    bal_color = "#10B981" if bal_ok else "#EF4444"
    bal_msg = (
        f"資產 {fmt(total_assets)} ＝ 負債 {fmt(total_liab)} + 權益 {fmt(total_eq)}"
    )

    return f"""
<div style="text-align:center;font-size:1.15rem;font-weight:700;
            color:#1E293B;padding:0.6rem 0 1rem;letter-spacing:0.03em">
  {latest_yr} 年度　資產負債表
</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;overflow-x:auto">
  <table style="{tbl_style}">
    <thead><tr><th style="{th_style}">科目</th><th style="{th_style}text-align:right">金額</th></tr></thead>
    <tbody>{asset_body}</tbody>
  </table>
  <table style="{tbl_style}">
    <thead><tr><th style="{th_style}">科目</th><th style="{th_style}text-align:right">金額</th></tr></thead>
    <tbody>{le_body}</tbody>
  </table>
</div>
<div style="text-align:center;padding:0.8rem 0 0.2rem;font-size:0.95rem;color:{bal_color};font-weight:600">
  {bal_icon} {bal_msg}
</div>"""


def generate_all_charts(d):
    """產生所有圖表 HTML，回傳 dict"""
    return dict(
        member_capital_trend=chart_member_capital_trend(d),
        loan_savings=chart_loan_savings(d),
        risk_trend=chart_risk_trend(d),
        ovd_full_history=chart_ovd_full_history(d),
        ovd_amount=chart_ovd_amount(d),
        waterfall=chart_waterfall(d),
        annual_trend=chart_annual_trend(d),
        balance_sheet=make_balance_sheet_html(d),
    )

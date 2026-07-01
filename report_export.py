import pandas as pd
from playwright.sync_api import sync_playwright
from report_config import THRESHOLDS, fmt, fmt_pct

def export_pdf(html_str, output_path):
    """
    載入 Playwright 無頭 Chromium
    將 HTML 字串載入並匯出為 A4 PDF
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.set_content(html_str)
        # 等待 Playwright/Plotly 圖表載入
        page.wait_for_load_state("networkidle")
        page.pdf(path=output_path, format="A4", print_background=True)
        browser.close()
    return output_path

def export_excel(d, output_path):
    """
    從 d["df_m"] / d["df_l"] 取出近 12 期資料
    用 pandas.ExcelWriter 寫入 3 個 sheet
    """
    recent_m = d["df_m"].sort_values("年月").tail(12).copy()
    recent_l = d["df_l"].sort_values("年月").tail(12).copy()

    # 將年月轉換為字串 'YYYY-MM' 以便於在 Excel 中閱讀
    recent_m["年月"] = recent_m["年月"].dt.strftime("%Y-%m")
    recent_l["年月"] = recent_l["年月"].dt.strftime("%Y-%m")

    # 保留所需的欄位
    df_sheet1 = recent_m[["年月", "社員數", "股金", "貸放比", "儲蓄率"]].copy()
    df_sheet2 = recent_l[["年月", "逾放比", "開支比", "提撥率"]].copy()

    # 計算 KPI 摘要
    rc = d.get("risk_count", 0)
    
    # 貸放比 YoY 計算
    df_m_data = d["df_m"]
    T1 = d["T1"]
    _m1 = df_m_data[df_m_data["年月"] <= T1].sort_values("年月")
    loan_prev = float(_m1["貸放比"].iloc[-1]) if not _m1.empty else None
    if loan_prev is not None:
        _ld = d["curr_eLoan"] - loan_prev
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
    elif prov_note == "無逾期":
        prov_value = "0.0%（無逾期）"
        prov_sub = "無逾期貸款，無需提撥"
    else:
        prov_value = fmt_pct(d["eProv"])
        prov_sub = f"{'充足 ✓' if prov_ok else '不足 ✗'}（門檻 {prov_thr * 100:.0f}%）"

    kpi_rows = [
        {"指標項目": "風險觸發數", "數值": f"{rc} / 5 條件", "說明": d["status"]},
        {"指標項目": "現有社員", "數值": f"{int(d['curr_M']):,} 人", "說明": f"12M {'↑' if d['memG_curr'] >= 0 else '↓'} {abs(int(d['curr_M'] - d['M0'])):,} 人 ({fmt_pct(d['memG_curr'])})"},
        {"指標項目": "現有股金", "數值": fmt(d["curr_S"]), "說明": f"12M {'↑' if d['shrG_curr'] >= 0 else '↓'} {fmt(abs(d['curr_S'] - d['S0']))} ({fmt_pct(d['shrG_curr'])})"},
        {"指標項目": "貸放比", "數值": fmt_pct(d["curr_eLoan"]), "說明": f"{'偏低' if d['curr_eLoan'] < 0.4 else '偏高' if d['curr_eLoan'] > 0.8 else '正常範圍'} (40–80%){loan_yoy}"},
        {"指標項目": "儲蓄率", "數值": fmt_pct(d["eRate"]), "說明": f"門檻 {sav_thr * 100:.0f}%，{'達標 ✓' if sav_ok else '未達標 ✗'}"},
        {"指標項目": "逾放比", "數值": fmt_pct(d["curr_eOvd"]), "說明": f"{'⚠ 警戒' if d['curr_eOvd'] > 0.02 else '✓ 正常'} (警戒值 2%)"},
        {"指標項目": "開支比(年)", "數值": fmt_pct(d["R0"]), "說明": f"{'⚠ 虧損' if d['R0'] > 1.0 else '✓ 盈餘'} (損益平衡 100%)"},
        {"指標項目": "提撥率", "數值": prov_value, "說明": prov_sub},
    ]
    df_sheet3 = pd.DataFrame(kpi_rows)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_sheet1.to_excel(writer, sheet_name="社務指標", index=False)
        df_sheet2.to_excel(writer, sheet_name="放款指標", index=False)
        df_sheet3.to_excel(writer, sheet_name="KPI 摘要", index=False)
    return output_path

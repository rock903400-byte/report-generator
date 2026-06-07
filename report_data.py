"""
讀取資料庫.xlsx + exported_data.csv，依社號過濾與計算指標
"""
import io
import pandas as pd
from report_config import (
    EXCEL_PATH, CSV_PATH, THRESHOLDS,
    convert_minguo_date, safe_div, get_value,
)

SHEETS = {
    "MAIN":   "社務及資金運用情形",
    "LOAN":   "放款及逾期放款",
    "REGION": "區域分類表",
}

def _clean_excel(df_m_raw, df_l_raw):
    """共用清洗邏輯"""
    df_m_raw["年月"] = df_m_raw["年月"].apply(convert_minguo_date)
    df_l_raw["年月"] = df_l_raw["年月"].apply(convert_minguo_date)

    for col in ["社員數", "股金", "貸放比"]:
        df_m_raw[col] = pd.to_numeric(df_m_raw[col], errors="coerce").fillna(0)

    df_m_raw["儲蓄率"] = pd.to_numeric(df_m_raw["儲蓄率"], errors="coerce").fillna(0)
    df_m_raw["儲蓄率"] = df_m_raw["儲蓄率"].apply(lambda x: x / 100 if abs(x) > 1.0 else x)

    df_l_raw["逾放比"]   = pd.to_numeric(df_l_raw["逾放比"],   errors="coerce").fillna(0)
    df_l_raw["逾期貸款"] = pd.to_numeric(df_l_raw["逾期貸款"], errors="coerce").fillna(0)
    df_l_raw["開支比"]   = pd.to_numeric(df_l_raw["開支比"],   errors="coerce").fillna(0)
    df_l_raw["開支比"]   = df_l_raw["開支比"].apply(lambda x: x / 100 if abs(x) > 5.0 else x)
    df_l_raw["提撥率"]   = pd.to_numeric(df_l_raw.get("提撥率", 0), errors="coerce").fillna(0)

    df_m = df_m_raw.dropna(subset=["年月"]).sort_values(["社號", "年月"])
    df_l = df_l_raw.dropna(subset=["年月"]).sort_values(["社號", "年月"])
    return df_m, df_l

def load_data_from_bytes(excel_bytes, csv_bytes=None):
    """從 BytesIO 載入資料（供雲端版使用）"""
    with pd.ExcelFile(io.BytesIO(excel_bytes)) as xls:
        df_m_raw = pd.read_excel(xls, sheet_name=SHEETS["MAIN"],   dtype={"社號": str, "年月": str})
        df_l_raw = pd.read_excel(xls, sheet_name=SHEETS["LOAN"],   dtype={"社號": str, "年月": str})
        df_r_raw = pd.read_excel(xls, sheet_name=SHEETS["REGION"], dtype={"社名": str, "區域": str, "密碼": str})
        df_l_raw = df_l_raw.rename(columns={"收支比": "開支比"})

    df_m, df_l = _clean_excel(df_m_raw, df_l_raw)

    df_csv = pd.DataFrame()
    if csv_bytes:
        try:
            df_csv = pd.read_csv(io.BytesIO(csv_bytes), dtype={"社號": str, "年月": str})
            df_csv["年月"] = df_csv["年月"].apply(convert_minguo_date)
            df_csv["當月金額"] = pd.to_numeric(df_csv["當月金額"], errors="coerce").fillna(0)
            df_csv["會計科目"] = df_csv["會計科目"].astype(str).str.replace(".0", "", regex=False)
        except Exception as e:
            print(f"  CSV 讀取失敗：{e}")

    return df_m, df_l, df_csv

def load_data():
    """載入 Excel + CSV（供本機 CLI 使用）"""
    print("讀取 Excel…")
    with open(EXCEL_PATH, "rb") as f:
        xls_bytes = f.read()

    print("讀取 CSV…")
    try:
        with open(CSV_PATH, "rb") as f:
            csv_bytes = f.read()
    except Exception as e:
        print(f"  CSV 讀取失敗：{e}")
        csv_bytes = None

    return load_data_from_bytes(xls_bytes, csv_bytes)

def extract_union_data(df_m, df_l, df_csv, union_id):
    """依社號提取單一合作社資料，回傳 dict"""
    union_m = df_m[df_m["社號"] == union_id].copy()
    union_l = df_l[df_l["社號"] == union_id].copy()

    if union_m.empty:
        raise ValueError(f"社號 {union_id} 在社務資料中無數據")

    s_name = union_m["社名"].iloc[0]
    s_no   = union_id
    print(f"找到：{s_name}（社號 {s_no}），共 {len(union_m)} 筆社務資料")

    union_csv = df_csv[df_csv["社號"] == union_id].copy() if not df_csv.empty else pd.DataFrame()
    has_csv = not union_csv.empty
    if has_csv:
        print(f"  CSV {s_name} 資料：{len(union_csv)} 筆")

    max_d = union_m["年月"].max()
    min_d = union_m["年月"].min()
    dec_dates = union_m[union_m["年月"].dt.month == 12]["年月"]
    T0 = dec_dates.max() if not dec_dates.empty else max_d
    T1 = max(T0 - pd.DateOffset(years=1), min_d)
    T2 = max(T0 - pd.DateOffset(years=2), min_d)
    T3 = max(T0 - pd.DateOffset(years=3), min_d)
    T_12M = max_d - pd.DateOffset(months=12)

    M0, M1, M2, M3 = (get_value(union_m, "社員數", t) for t in (T0, T1, T2, T3))
    S0, S1, S2, S3 = (get_value(union_m, "股金",   t) for t in (T0, T1, T2, T3))
    R0, R1 = get_value(union_l, "開支比", T0), get_value(union_l, "開支比", T1)
    O0, O1 = get_value(union_l, "逾期貸款", T0), get_value(union_l, "逾期貸款", T1)
    eOvd   = get_value(union_l, "逾放比", T0)
    eLoan  = get_value(union_m, "貸放比", T0)
    eRate  = get_value(union_m, "儲蓄率", max_d)
    eProv  = float(union_l.iloc[-1]["提撥率"]) if not union_l.empty else 0.0
    memG   = safe_div(M0 - M1, M1)
    shrG   = safe_div(S0 - S1, S1)

    curr_M = get_value(union_m, "社員數", max_d)
    curr_S = get_value(union_m, "股金",   max_d)
    memG_curr = safe_div(curr_M - M0, M0)
    shrG_curr = safe_div(curr_S - S0, S0)
    eOvd_12m  = get_value(union_l, "逾放比", T_12M)

    # ── 風險診斷（2/5 原則）─────────────────────────────
    flags = []
    notes = []
    c1 = R0 > THRESHOLDS["high_risk_income_ratio"] and R1 > THRESHOLDS["high_risk_income_ratio"]
    c2 = eLoan < THRESHOLDS["high_risk_loan_ratio"]
    c3 = eOvd > THRESHOLDS["high_risk_ovd_ratio"] and O0 > O1
    c4 = M0 < M1 < M2 < M3
    c5 = S0 < S1 < S2 < S3
    risk_count = sum([c1, c2, c3, c4, c5])

    if c1: notes.append("連兩年虧損")
    if c2: notes.append("貸放比偏低")
    if c3: notes.append("逾放比偏高且惡化")
    if c4: notes.append("社員連三年衰退")
    if c5: notes.append("股金連三年衰退")

    if risk_count >= 2:
        status = "🚨 重點輔導"
        status_color = "#EF4444"
    elif eLoan > THRESHOLDS["liquidity_loan"] and shrG < 0:
        status = "⚠️ 流動性緊繃"
        status_color = "#F59E0B"
    elif eLoan < THRESHOLDS["idle_loan"] and eOvd < THRESHOLDS["ovd_safe_line"]:
        status = "💤 資金閒置"
        status_color = "#3B82F6"
    elif (memG >= 0 and shrG >= 0
          and THRESHOLDS["stable_loan_min"] <= eLoan <= THRESHOLDS["stable_loan_max"]
          and eOvd < THRESHOLDS["ovd_safe_line"]):
        status = "✅ 穩健模範"
        status_color = "#10B981"
    else:
        status = "📊 一般狀態"
        status_color = "#64748B"

    reason_text = "、".join(notes) if notes else "各項指標正常"

    return dict(
        s_no=s_no, s_name=s_name, max_d=max_d, min_d=min_d,
        T0=T0, T1=T1, T2=T2, T3=T3, T_12M=T_12M,
        df_m=union_m, df_l=union_l, df_csv=union_csv, has_csv=has_csv,
        M0=M0, M1=M1, M2=M2, M3=M3,
        S0=S0, S1=S1, S2=S2, S3=S3,
        R0=R0, R1=R1, O0=O0, O1=O1,
        eOvd=eOvd, eLoan=eLoan, eRate=eRate, eProv=eProv,
        memG=memG, shrG=shrG,
        curr_M=curr_M, curr_S=curr_S,
        memG_curr=memG_curr, shrG_curr=shrG_curr,
        eOvd_12m=eOvd_12m,
        status=status, status_color=status_color,
        reason_text=reason_text, notes=notes, risk_count=risk_count,
    )

def compute_ovd_stats(d):
    """逾放比統計摘要"""
    df = d["df_l"][["年月", "逾放比", "提撥率"]].copy()
    WARN = THRESHOLDS["ovd_safe_line"]
    curr = float(df["逾放比"].iloc[-1])
    avg12 = float(df["逾放比"].tail(12).mean())
    hist_max = float(df["逾放比"].max())
    hist_max_d = df.loc[df["逾放比"].idxmax(), "年月"].strftime("%Y-%m") if not df.empty else ""
    hist_min = float(df["逾放比"].min())
    hist_min_d = df.loc[df["逾放比"].idxmin(), "年月"].strftime("%Y-%m") if not df.empty else ""
    months_warn = int((df["逾放比"] > WARN).sum())
    months_total = len(df)

    last6 = df["逾放比"].tail(6)
    slope = float(last6.iloc[-1] - last6.iloc[0]) if len(last6) >= 2 else 0.0
    trend = "持續改善" if slope < -0.001 else ("持續惡化" if slope > 0.001 else "趨於穩定")
    trend_color = "#10B981" if slope < -0.001 else ("#EF4444" if slope > 0.001 else "#64748B")

    prov_curr = float(df["提撥率"].iloc[-1])
    coverage = safe_div(prov_curr, curr) if curr > 0 else 0.0

    return dict(
        curr=curr, avg12=avg12, hist_max=hist_max, hist_max_d=hist_max_d,
        hist_min=hist_min, hist_min_d=hist_min_d,
        months_warn=months_warn, months_total=months_total,
        trend=trend, trend_color=trend_color,
        prov_curr=prov_curr, coverage=coverage,
    )

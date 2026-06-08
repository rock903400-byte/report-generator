"""
讀取資料庫.xlsx + exported_data.csv，依社號過濾與計算指標
"""
import sys
from pathlib import Path
_root = str(Path(__file__).resolve().parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import io
import pandas as pd
from report_config import (
    EXCEL_PATH, CSV_PATH, THRESHOLDS,
    convert_minguo_date, safe_div, get_value,
)
from common.cleaning import defensive_clean_series
from common.classifier import classify

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

    df_m_raw["儲蓄率"] = defensive_clean_series(
        pd.to_numeric(df_m_raw["儲蓄率"], errors="coerce").fillna(0), "儲蓄率"
    )
    df_l_raw["逾放比"]   = pd.to_numeric(df_l_raw["逾放比"],   errors="coerce").fillna(0)
    df_l_raw["逾期貸款"] = pd.to_numeric(df_l_raw["逾期貸款"], errors="coerce").fillna(0)
    df_l_raw["開支比"]   = defensive_clean_series(
        pd.to_numeric(df_l_raw["開支比"], errors="coerce").fillna(0), "開支比"
    )
    df_l_raw["提撥率"]   = pd.to_numeric(df_l_raw.get("提撥率", 0), errors="coerce").fillna(0)

    df_m = df_m_raw.dropna(subset=["年月"]).sort_values(["社號", "年月"])
    df_l = df_l_raw.dropna(subset=["年月"]).sort_values(["社號", "年月"])
    return df_m, df_l

def load_data_from_bytes(excel_bytes, csv_bytes=None):
    """從 BytesIO 載入資料（供雲端版使用）"""
    try:
        with pd.ExcelFile(io.BytesIO(excel_bytes)) as xls:
            sheet_names = xls.sheet_names
            for key, name in SHEETS.items():
                if name not in sheet_names:
                    raise ValueError(
                        f"Excel 缺少工作表「{name}」（應為 {list(SHEETS.values())}）"
                    )
            df_m_raw = pd.read_excel(xls, sheet_name=SHEETS["MAIN"],   dtype={"社號": str, "年月": str})
            df_l_raw = pd.read_excel(xls, sheet_name=SHEETS["LOAN"],   dtype={"社號": str, "年月": str})
            df_r_raw = pd.read_excel(xls, sheet_name=SHEETS["REGION"], dtype={"社名": str, "區域": str, "密碼": str})
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(
            f"無法讀取 Excel 檔案，請確認上傳的是正確的「資料庫.xlsx」（{e}）"
        ) from e

    df_l_raw = df_l_raw.rename(columns={"收支比": "開支比"})
    required_m = {"社號", "社名", "年月", "社員數", "股金", "貸放比", "儲蓄率"}
    missing_m = required_m - set(df_m_raw.columns)
    if missing_m:
        raise ValueError(
            f"社務資料工作表缺少欄位：{', '.join(sorted(missing_m))}"
        )
    required_l = {"社號", "社名", "年月", "開支比", "逾放比", "逾期貸款"}
    missing_l = required_l - set(df_l_raw.columns)
    if missing_l:
        raise ValueError(
            f"放款資料工作表缺少欄位：{', '.join(sorted(missing_l))}"
        )

    df_m, df_l = _clean_excel(df_m_raw, df_l_raw)

    if df_m.empty:
        raise ValueError("清洗後社務資料無有效資料，請檢查「年月」格式是否正確（應為 5 碼民國年月，如 11504）")

    df_csv = pd.DataFrame()
    if csv_bytes:
        try:
            df_csv = pd.read_csv(io.BytesIO(csv_bytes), encoding="utf-8-sig", dtype={"社號": str, "年月": str})
            required_csv = {"年月", "社號", "會計科目", "當月金額"}
            if not required_csv.issubset(set(df_csv.columns)):
                missing_csv = required_csv - set(df_csv.columns)
                print(f"  CSV 缺少必要欄位：{', '.join(sorted(missing_csv))}，跳過 CSV")
                df_csv = pd.DataFrame()
            else:
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
    """依社號提取單一儲互社資料，回傳 dict"""
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
    eProv  = float(union_l["提撥率"].iloc[-1]) if not union_l.empty and "提撥率" in union_l.columns else 0.0
    memG   = safe_div(M0 - M1, M1)
    shrG   = safe_div(S0 - S1, S1)

    curr_M = get_value(union_m, "社員數", max_d)
    curr_S = get_value(union_m, "股金",   max_d)
    memG_curr = safe_div(curr_M - M0, M0)
    shrG_curr = safe_div(curr_S - S0, S0)
    eOvd_12m  = get_value(union_l, "逾放比", T_12M)

    # ── 風險診斷（2/5 原則）─────────────────────────────
    STATUS_COLORS = {
        "🚨 特別關懷": "#EF4444",
        "⚠️ 流動性緊繃": "#F59E0B",
        "💤 資金閒置": "#3B82F6",
        "✅ 穩健模範": "#10B981",
        "📊 一般狀態": "#64748B",
    }
    p = dict(M0=M0, M1=M1, M2=M2, M3=M3, S0=S0, S1=S1, S2=S2, S3=S3,
             R0=R0, R1=R1, O0=O0, O1=O1, eOvd=eOvd, eLoan=eLoan,
             sOvd=get_value(union_l, "逾放比", T1),
             sLoan=get_value(union_m, "貸放比", T1),
             memG=memG, shrG=shrG)
    status, reason_text = classify(p, THRESHOLDS)
    status_color = STATUS_COLORS.get(status, "#64748B")

    # 保留 notes + risk_count 給模板用
    c1 = R0 > THRESHOLDS["high_risk_income_ratio"] and R1 > THRESHOLDS["high_risk_income_ratio"]
    c2 = eLoan < THRESHOLDS["high_risk_loan_ratio"]
    c3 = eOvd > THRESHOLDS["high_risk_ovd_ratio"] and O0 > O1
    c4 = M0 < M1 < M2 < M3
    c5 = S0 < S1 < S2 < S3
    notes = []
    if c1: notes.append("連兩年虧損")
    if c2: notes.append("貸放比過低")
    if c3: notes.append("高逾放且惡化")
    if c4: notes.append("人數連三年衰退")
    if c5: notes.append("股金連三年衰退")
    risk_count = sum([c1, c2, c3, c4, c5])

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
    df_l = d["df_l"]
    if df_l.empty or not {"年月", "逾放比", "提撥率"}.issubset(df_l.columns):
        empty = dict(curr=0, avg12=0, hist_max=0, hist_max_d="", hist_min=0, hist_min_d="",
                     months_warn=0, months_total=0, trend="無資料", trend_color="#64748B",
                     prov_curr=0, coverage=0)
        if df_l.empty:
            return empty
        try:
            df = df_l[["年月", "逾放比", "提撥率"]].copy()
        except KeyError:
            return empty
    else:
        df = df_l[["年月", "逾放比", "提撥率"]].copy()
    if df.empty:
        return dict(curr=0, avg12=0, hist_max=0, hist_max_d="", hist_min=0, hist_min_d="",
                    months_warn=0, months_total=0, trend="無資料", trend_color="#64748B",
                    prov_curr=0, coverage=0)
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

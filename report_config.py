"""
報告工具全域配置
"""
import streamlit as st
import pandas as pd

# ── 33 社完整對照表 ──────────────────────────────────────────
REGIONS = {
    "雲林": [
        (3201, "百成"), (3202, "伯鐸"), (3203, "福祿"), (3204, "鹿寮"),
        (3205, "路加"), (3206, "聖三"), (3207, "崙光"), (3208, "豪友"),
        (3210, "惠民"), (3211, "愛心"), (3212, "上智"), (3213, "二崙"),
        (3214, "德化"),
    ],
    "嘉義": [
        (3301, "民權"), (3305, "義德"), (3307, "福民"),
        (3401, "鹿草"), (3402, "聖母"), (3403, "海星"), (3404, "玉山"),
        (3406, "救主"), (3407, "樂野"), (3408, "主恩"), (3409, "三育"),
        (3410, "里山"), (3411, "山美"), (3412, "新美"), (3413, "達邦"),
        (3414, "新光"), (3415, "民光"), (3416, "來吉"), (3417, "茶山"),
    ],
}

def get_all_unions():
    """回傳 [(社號, 社名, 區域), ...]"""
    result = []
    for region, unions in REGIONS.items():
        for sid, sname in unions:
            result.append((sid, sname, region))
    return result

def find_union(keyword):
    """依社名或社號搜尋，回傳 (社號, 社名, 區域) 或 None"""
    kw = keyword.strip().replace("社", "")
    for region, unions in REGIONS.items():
        for sid, sname in unions:
            if str(sid) == kw or sname == kw:
                return (sid, sname, region)
    return None

# ── 檔案路徑 ──────────────────────────────────────────────────
EXCEL_PATH = "../下載工具/資料庫.xlsx"
CSV_PATH   = "../下載工具/exported_data.csv"

# ── 門檻值（從 st.secrets 讀取，與 deploy 同步；本機無 secrets 時用預設值）─────
_THR_DEFAULTS = {
    "high_risk_ovd": 0.1, "liquidity_loan": 0.9, "idle_loan": 0.3,
    "stable_loan_min": 0.4, "stable_loan_max": 0.8, "ovd_safe_line": 0.02,
    "high_risk_income_ratio": 1.0, "high_risk_loan_ratio": 0.1, "high_risk_ovd_ratio": 0.5,
    "savings_good": 0.6, "provision_good": 0.01,
}

def _load_thresholds():
    try:
        thr = st.secrets.get("thresholds", {})
    except Exception:
        thr = {}
    return {k: thr.get(k, d) for k, d in _THR_DEFAULTS.items()}

THRESHOLDS = _load_thresholds()

# ── Gemini AI ──────────────────────────────────────────────────
GEMINI_MODEL = "gemini-3.5-flash"

# ── 主題色 ────────────────────────────────────────────────────
THEME_BG = "#F0F4F8"
C = {
    "green":  "#10B981",
    "red":    "#EF4444",
    "blue":   "#3B82F6",
    "amber":  "#F59E0B",
    "indigo": "#6366F1",
    "slate":  "#64748B",
    "text":   "#1E293B",
}

PLOTLY_CFG = dict(
    displayModeBar=True,
    modeBarButtons=[["toImage"]],
    displaylogo=False,
    toImageButtonOptions={"format": "png", "scale": 3},
)

# ── 工具函式 ──────────────────────────────────────────────────
def convert_minguo_date(val):
    try:
        s = str(int(float(str(val).strip())))
        if len(s) == 5:
            yr, mo = int(s[:3]) + 1911, int(s[3:])
        elif len(s) == 4:
            yr, mo = int(s[:2]) + 1911, int(s[2:])
        else:
            return pd.NaT
        return pd.to_datetime(f"{yr}-{mo:02d}-01")
    except Exception:
        return pd.NaT

def safe_div(n, d):
    try:
        if d and not pd.isna(d) and d != 0:
            return n / d
    except Exception:
        pass
    return 0.0

def fmt(n, decimals=2):
    try:
        n = float(n)
        if abs(n) >= 1e8:
            return f"{n/1e8:.{decimals}f} 億元"
        if abs(n) >= 1e4:
            return f"{n/1e4:.0f} 萬元"
        return f"{n:,.0f} 元"
    except Exception:
        return str(n)

def fmt_pct(v, decimals=1):
    try:
        return f"{float(v)*100:.{decimals}f}%"
    except Exception:
        return "—"

def get_value(df, col, d):
    if df.empty:
        return 0.0
    sub = df[df["年月"] <= d]
    return float(sub[col].iloc[-1]) if not sub.empty else float(df[col].iloc[0])

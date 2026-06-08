"""
報告工具全域配置
"""
import sys
from pathlib import Path
_root = str(Path(__file__).resolve().parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st

from common.thresholds import load_thresholds, DEFAULT_THRESHOLDS
from common.dates import convert_minguo_date, get_value
from common.utils import safe_div, format_large_number as fmt, fmt_pct

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
def _load_thresholds():
    try:
        return load_thresholds(st.secrets)
    except Exception:
        return load_thresholds({})

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

# ── 工具函式 (re-exported from common) ───────────────────────
# convert_minguo_date, safe_div, fmt, fmt_pct, get_value 均由上方 import 提供

"""
報告工具全域配置

REGIONS 從 st.secrets 讀取真實單位對照表；
無 secrets 時回退到虛構示範資料，不洩漏真實機構名稱。
"""

import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st  # noqa: E402

from common.thresholds import load_thresholds  # noqa: E402
from common.dates import convert_minguo_date, get_value  # noqa: E402, F401
from common.utils import safe_div, format_large_number as fmt, fmt_pct  # noqa: E402, F401

# ── 示範單位對照表（無 secrets 時的回退值，全為虛構名稱）───────────
_FALLBACK_REGIONS = {
    "北區": [
        (1101, "晨光"),
        (1102, "青川"),
        (1103, "柏原"),
        (1104, "明泉"),
        (1105, "松嶺"),
        (1106, "澄海"),
        (1107, "遠山"),
        (1108, "初丘"),
    ],
    "中區": [
        (1201, "和霖"),
        (1202, "南岑"),
        (1203, "白鷺"),
        (1204, "昭陽"),
        (1205, "綠汀"),
        (1206, "沐風"),
        (1207, "石橋"),
        (1208, "長洲"),
    ],
    "南區": [
        (1301, "雲棲"),
        (1302, "朝露"),
        (1303, "楓津"),
        (1304, "靜安"),
        (1305, "錦屏"),
        (1306, "藍嶼"),
        (1307, "芸台"),
        (1308, "芷汀"),
    ],
    "東區": [
        (1401, "星野"),
        (1402, "岩汀"),
        (1403, "木蘭"),
        (1404, "溪畔"),
        (1405, "曦谷"),
        (1406, "霜白"),
        (1407, "遙川"),
        (1408, "北衍"),
    ],
    "離島區": [
        (1501, "潮生"),
        (1502, "汐留"),
        (1503, "嶼安"),
        (1504, "灣澳"),
        (1505, "礁川"),
        (1506, "浪岐"),
        (1507, "霧津"),
        (1508, "岸沐"),
    ],
}


def _load_regions():
    """從 st.secrets 載入真實單位對照表；無 secrets 時回退到虛構示範資料。"""
    try:
        raw = st.secrets.get("regions", None)
        if not raw:
            return _FALLBACK_REGIONS
        return {k: [tuple(x) for x in v] for k, v in raw.items()}
    except Exception:
        return _FALLBACK_REGIONS


REGIONS = _load_regions()


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
CSV_PATH = "../下載工具/exported_data.csv"


# ── 門檻值（從 st.secrets 讀取，與 deploy 同步；本機無 secrets 時用預設值）─────
def _load_thresholds():
    try:
        return load_thresholds(st.secrets)
    except Exception:
        return load_thresholds({})


THRESHOLDS = _load_thresholds()

# ── Gemini AI ──────────────────────────────────────────────────
GEMINI_MODEL = "gemini-3.8-flash"

# ── 主題色 ────────────────────────────────────────────────────
THEME_BG = "#F0F4F8"
C = {
    "green": "#10B981",
    "red": "#EF4444",
    "blue": "#3B82F6",
    "amber": "#F59E0B",
    "indigo": "#6366F1",
    "slate": "#64748B",
    "text": "#1E293B",
}

PLOTLY_CFG = dict(
    displayModeBar=True,
    modeBarButtons=[["toImage"]],
    displaylogo=False,
    toImageButtonOptions={"format": "png", "scale": 3},
)

# ── 工具函式 (re-exported from common) ───────────────────────
# convert_minguo_date, safe_div, fmt, fmt_pct, get_value 均由上方 import 提供

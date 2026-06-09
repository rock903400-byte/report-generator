"""
報告工具全域配置
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

# ── 105 社完整對照表 ──────────────────────────────────────────
REGIONS = {
    "雲林": [
        (3201, "百成"),
        (3202, "伯鐸"),
        (3203, "福祿"),
        (3204, "鹿寮"),
        (3205, "路加"),
        (3206, "聖三"),
        (3207, "崙光"),
        (3208, "豪友"),
        (3210, "惠民"),
        (3211, "愛心"),
        (3212, "上智"),
        (3213, "二崙"),
        (3214, "德化"),
    ],
    "嘉義": [
        (3301, "民權"),
        (3305, "義德"),
        (3307, "福民"),
        (3401, "鹿草"),
        (3402, "聖母"),
        (3403, "海星"),
        (3404, "玉山"),
        (3406, "救主"),
        (3407, "樂野"),
        (3408, "主恩"),
        (3409, "三育"),
        (3410, "里山"),
        (3411, "山美"),
        (3412, "新美"),
        (3413, "達邦"),
        (3414, "新光"),
        (3415, "民光"),
        (3416, "來吉"),
        (3417, "茶山"),
    ],
    "台中": [
        (2201, "道明"),
        (2202, "雅敬"),
        (2204, "水湳"),
        (2205, "西屯"),
        (2207, "衛道"),
        (2208, "中南"),
        (2209, "向上"),
        (2210, "中聖"),
        (2211, "約瑟"),
        (2212, "傳愛"),
        (2213, "磊川"),
        (2214, "草生"),
        (2301, "東勢"),
        (2302, "信愛"),
        (2303, "大甲"),
        (2305, "峰谷"),
        (2306, "天僑"),
        (2314, "磐頂"),
        (2315, "弗傳慈心"),
    ],
    "南投": [
        (2401, "眉溪"),
        (2402, "鹿谷"),
        (2403, "秀峰"),
        (2405, "竹山"),
        (2406, "中州"),
        (2407, "聖愛"),
        (2408, "羅娜"),
        (2409, "春陽"),
        (2410, "親愛"),
        (2411, "啟德"),
        (2412, "愛德"),
        (2413, "世光"),
        (2414, "華德"),
        (2415, "萬豐"),
        (2416, "主愛"),
        (2417, "敬宗"),
        (2419, "久美"),
        (2420, "武界"),
        (2421, "人倫"),
        (2422, "埔里"),
        (2423, "中正"),
        (2424, "芳蘭"),
        (2426, "豐丘"),
        (2427, "新鄉"),
        (2429, "望鄉"),
        (2430, "東埔"),
        (2432, "雙龍"),
        (2433, "潭南"),
        (2434, "雙豐"),
        (2436, "力行"),
        (2437, "十方"),
        (2438, "發祥"),
        (2439, "清流"),
        (2440, "日月潭"),
    ],
    "彰化": [
        (3101, "永祥"),
        (3102, "聖神"),
        (3103, "合興"),
        (3104, "聖家"),
        (3106, "多加"),
        (3107, "佳信"),
        (3108, "永生"),
        (3109, "仁德"),
        (3110, "德華"),
        (3111, "竹塘"),
        (3112, "天民"),
        (3115, "新吉"),
        (3116, "榮星"),
        (3118, "永福"),
        (3119, "同心"),
        (3121, "和平"),
        (3122, "愛助"),
        (3123, "平安"),
        (3124, "樂仁"),
        (3127, "海豐"),
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
CSV_PATH = "../下載工具/exported_data.csv"


# ── 門檻值（從 st.secrets 讀取，與 deploy 同步；本機無 secrets 時用預設值）─────
def _load_thresholds():
    try:
        return load_thresholds(st.secrets)
    except Exception:
        return load_thresholds({})


THRESHOLDS = _load_thresholds()

# ── Gemini AI ──────────────────────────────────────────────────
GEMINI_MODEL = "gemini-2.5-flash"

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

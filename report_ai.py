"""
儲互社 AI 顧問分析（Gemini 串接）
"""
from google import genai
from google.genai import types
from report_config import GEMINI_MODEL, fmt, fmt_pct

_SYSTEM = """你是一位台灣儲蓄互助社財務顧問。請用繁體中文產出精簡扼要的分析（控制在 250 字內），採無序列表呈現，每項一行：

整體而言，本社財務體質屬 [健康/注意/危險]。以下為關鍵觀察：

- **亮點**：[若無則寫「無」]
- **風險**：[若有則逐項列出，附數值]
- **建議**：[最多 2 項可操作行動]

規則：
- 引用數據務必附實際數值，例如「貸放比 16.3%」
- 善用 3 年趨勢判斷方向（惡化中/改善中/持平）
- 語氣專業、客觀，不編造數字
- 若該社無明顯風險，直接告知「無顯著風險」即可"""


def build_ai_prompt(d):
    """從 d dict 組出中文 prompt"""
    m_trend = f"{int(d['M3']):,} → {int(d['M2']):,} → {int(d['M1']):,} → {int(d['M0']):,}"
    s_trend = f"{fmt(d['S3'])} → {fmt(d['S2'])} → {fmt(d['S1'])} → {fmt(d['S0'])}"
    r_trend = f"{fmt_pct(d['R1'])} → {fmt_pct(d['R0'])}"

    return f"""{_SYSTEM}

=== 基本資料 ===
社名：{d['s_name']}（社號 {d['s_no']}）
資料截至：{d['max_d'].strftime('%Y年%m月')}

=== 核心指標 ===
社員數：{int(d['curr_M']):,} 人（12M {fmt_pct(d['memG_curr'])}）
股金：{fmt(d['curr_S'])}（12M {fmt_pct(d['shrG_curr'])}）
貸放比：{fmt_pct(d['eLoan'])}（健康範圍 40–80%）
儲蓄率：{fmt_pct(d['eRate'])}
逾放比：{fmt_pct(d['eOvd'])}（警戒值 2%）
開支比（年）：{fmt_pct(d['R0'])}（>100% 為虧損）
提撥率：{fmt_pct(d['eProv'])}

=== 風險診斷 ===
狀態：{d['status']}
觸發事項：{d['reason_text']}

=== 3 年趨勢 ===
社員數：{m_trend}
股金：{s_trend}
開支比：{r_trend}"""


def call_gemini(prompt, api_key):
    """呼叫 Gemini API，回傳分析文字"""
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.4,
            max_output_tokens=600,
        ),
    )
    return response.text


def analyze_with_gemini(d, api_key=""):
    """主入口；失敗回傳 None"""
    if not api_key:
        return None
    try:
        prompt = build_ai_prompt(d)
        return call_gemini(prompt, api_key)
    except Exception as e:
        print(f"  AI 分析失敗：{e}")
        return None

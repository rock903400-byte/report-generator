"""
儲互社 AI 顧問分析（Gemini 串接）
"""
from google import genai
from google.genai import types
from report_config import GEMINI_MODEL, fmt, fmt_pct

_SYSTEM = """你是一位專精於台灣儲蓄互助社（儲互社）的財務顧問。請根據以下財務數據，用繁體中文產出完整的顧問分析，包含以下段落：

1. **整體評價** — 用一句話總結該社當前財務體質（健康/注意/危險）
2. **值得肯定的亮點** — 舉出具體數據說明強項（如儲蓄率、提撥率、社員忠誠度等）
3. **需要關注的風險** — 逐項指出超標或惡化的指標，附上實際數值，含連續趨勢判斷：
   - 社員與股金是否持續衰退
   - 貸放比是否偏離健康區間（40%–80%）
   - 逾放比是否超過警戒值（2%）
   - 開支比是否接近或超過損益平衡點（100%）
4. **具體建議** — 根據上述風險，給出可操作的改善行動方案

分析要求：
- 引用數據時明確附上數值，例如「貸放比 16.3%，遠低於健康區間」
- 善用 3 年趨勢判斷方向（惡化中/改善中/持平）
- 語氣專業、客觀、具體
- 不要編造不存在的數字"""


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
            max_output_tokens=4096,
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

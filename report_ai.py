"""
儲互社 AI 顧問分析（Gemini 串接）
"""
from google import genai
from google.genai import types
from report_config import GEMINI_MODEL, fmt, fmt_pct

_SYSTEM = """你是儲互社財務顧問。請根據以下合作社的最新財務數據，用繁體中文、條理分明的方式，給出 300 字內的顧問分析，包含三段：

1. 整體評價（一句話）
2. 值得肯定的亮點（最多 2 點）
3. 需要關注的風險與建議（最多 3 點）

不要編造數字，只根據以下資料回應。"""


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
            max_output_tokens=800,
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

"""
儲互社 AI 顧問分析（Gemini 串接）
"""
from google import genai
from google.genai import types
from report_config import GEMINI_MODEL, fmt, fmt_pct

_SYSTEM = """你是一位台灣儲蓄互助社資深財務顧問。請用繁體中文產出專業財務分析報告，採用以下結構：

## 一、財務健康評分卡
| 維度 | 評分 | 狀態 | 關鍵數據 |
|------|------|------|----------|
| 成長性 | X/10 | ↑改善/→持平/↓惡化 | 社員數 3Y 變化 X%、股金 3Y 變化 X% |
| 資產品質 | X/10 | ↑改善/→持平/↓惡化 | 逾放比 X%（門檻 2%）、提撥率 X% |
| 獲利能力 | X/10 | ↑改善/→持平/↓惡化 | 開支比 X%（<100% 盈餘） |
| 流動性 | X/10 | ↑改善/→持平/↓惡化 | 貸放比 X%（健康 40-80%）、儲蓄率 X% |

**總體評分：X/10** — [一句話總結]

## 二、風險評估（按嚴重程度排序）
1. **[風險名稱]** — 嚴重度：高/中/低
   - 現況：[引用數據]
   - 趨勢：[3 年變化]
   - 建議：[具體行動]

## 三、量化改善建議
1. **[行動]**
   - 目標：[具體數字]
   - 計算：[公式，如：需增加放款 = 儲蓄額 × 60% - 現有放款]
   - 預期效益：[指標從 X% 改善至 Y%]
   - 時間框架：[3M/6M/1Y]

## 四、亮點
- [若有顯著優勢，列出 1-2 項]

規則：
- 評分標準：成長性（3Y 社員成長 >10% → 8-10 分；<0% → 1-4 分）；資產品質（逾放比 <1% → 9-10 分；>5% → 1-2 分）；獲利（開支比 <90% → 8-10 分；>100% → 1-4 分）；流動性（貸放比 40-80% → 8-10 分；<30% 或 >90% → 1-4 分）
- 引用數據必須為實際數值，不可編造
- 建議必須包含可計算的公式或門檻
- 若無顯著風險，直接告知「財務體質健全，無顯著風險」
- 總字數控制在 500 字內"""


def build_ai_prompt(d):
    """從 d dict 組出中文 prompt"""
    m_trend = f"{int(d['M3']):,} → {int(d['M2']):,} → {int(d['M1']):,} → {int(d['M0']):,}"
    s_trend = f"{fmt(d['S3'])} → {fmt(d['S2'])} → {fmt(d['S1'])} → {fmt(d['S0'])}"
    r_trend = f"{fmt_pct(d['R1'])} → {fmt_pct(d['R0'])}"

    prov_note = d.get("eProv_note", "")
    if prov_note == "資料缺失":
        prov_text = "無資料（原始缺漏）"
    elif prov_note == "無逾期":
        prov_text = "0.0%（無逾期貸款）"
    else:
        prov_text = fmt_pct(d["eProv"])

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
提撥率：{prov_text}

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
            max_output_tokens=2048,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
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

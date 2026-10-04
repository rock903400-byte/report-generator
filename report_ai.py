"""
儲互社 AI 顧問分析（Gemini 串接）
"""

from report_config import GEMINI_MODEL, fmt, fmt_pct

_SYSTEM = """語氣：專業、客觀、簡潔，像寫給理事會的內部報告。

請用繁體中文產出專業財務分析報告，採用以下結構：

## 一、財務健康評分卡

- **成長性：X/10** ↑改善/→持平/↓惡化
  - 社員數 3Y 變化 X%（N→M 人）
  - 股金 3Y 變化 X%（N 萬→M 萬）
- **資產品質：X/10** ↑改善/→持平/↓惡化
  - 逾放比 X%（上限 5%）
  - 提撥率 X%
- **獲利能力：X/10** ↑改善/→持平/↓惡化
  - 開支比 X%（<100% 盈餘）
- **流動性：X/10** ↑改善/→持平/↓惡化
  - 貸放比 X%（健康 40-80%）
  - 儲蓄率 X%

**總體評分：X/10** — [一句話總結]
（計算方式：四維度平均，資產品質權重 1.5 倍）

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

評分標準：
- 成長性：3Y 社員成長 >10% → 8-10 分；0-10% → 5-7 分；<0% → 1-4 分
- 資產品質：逾放比 <1% → 9-10 分；1-5% → 4-8 分；>5% → 1-3 分
  （1% 對應金管會優等線，5% 對應 PEARLS 上限）
- 獲利能力：開支比 <90% → 8-10 分；90-100% → 5-7 分；>100% → 1-4 分
- 流動性：貸放比 40-80% → 8-10 分；30-40% 或 80-90% → 5-7 分；<30% 或 >90% → 1-4 分

規則：
- 引用數據必須為實際數值，不可編造
- 建議必須包含可計算的公式或門檻
- 若資料不足 3 年，以實際可用年數評估並註明
- 若無顯著風險，直接告知「財務體質健全，無顯著風險」
- 總字數控制在 600 字內"""


def build_ai_prompt(d):
    """從 d dict 組出中文 prompt（時點指標一律用最新月 curr_*，並標註截至年月）"""
    m_trend = f"{int(d['M3']):,} → {int(d['M2']):,} → {int(d['M1']):,} → {int(d['M0']):,}"
    s_trend = f"{fmt(d['S3'])} → {fmt(d['S2'])} → {fmt(d['S1'])} → {fmt(d['S0'])}"
    r_trend = f"{fmt_pct(d['R1'])} → {fmt_pct(d['R0'])}"
    data_end = d["max_d"].strftime("%Y年%m月")
    t0_year = f"民{d['T0'].year - 1911}年度"

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
    貸放比：{fmt_pct(d['curr_eLoan'])}（健康範圍 40–80%，截至{data_end}）
    儲蓄率：{fmt_pct(d['eRate'])}（截至{data_end}）
    逾放比：{fmt_pct(d['curr_eOvd'])}（PEARLS 上限 5%，截至{data_end}）
    開支比（{t0_year}）：{fmt_pct(d['R0'])}（>100% 為虧損）
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
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        # 3.x Flash 不支援 temperature / thinking_budget（server 報錯）；
        # 用 thinking_level LOW 保持低延遲（原 thinking_budget=0 的對應做法）。
        config=types.GenerateContentConfig(
            max_output_tokens=2048,
            thinking_config=types.ThinkingConfig(thinking_level="LOW"),
        ),
    )
    return response.text


def analyze_with_gemini(d, api_key=""):
    """主入口；失敗回傳 (None, error_msg)"""
    if not api_key:
        return None, "未設定 API Key"
    try:
        prompt = build_ai_prompt(d)
        result = call_gemini(prompt, api_key)
        return result, None
    except Exception as e:
        return None, str(e)

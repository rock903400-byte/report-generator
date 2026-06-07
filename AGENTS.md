# AGENTS.md — 報告工具

## Git 追蹤狀態（重要）

**只有 8 個檔案會上 GitHub / Streamlit Cloud：**
`app.py` `report_config.py` `report_data.py` `report_charts.py` `report_html.py` `report_ai.py` `requirements.txt` `AGENTS.md`

**以下全部 gitignore，僅本機存在：**
`generate_report.py` `app_report.py` `app_cloud.py` `generate_dabang_report.py` `verify_data.py` `verify_full.py` `check_html.py` `output/` `.streamlit/secrets.toml`

改完 `report_*.py` 或 `app.py` 後 `git add && git push`，Streamlit Cloud 1–3 分鐘自動部署。

## 兩套子系統

| 系統 | 入口 | 備註 |
|------|------|------|
| **Plotly 新系統** | `app.py`（雲端）/ `app_report.py`（本機）/ `generate_report.py`（CLI） | 支援 33 社，可改 |
| **舊靜態報告** | `generate_dabang_report.py` | **勿修改**，內嵌整套邏輯 |

## 常用指令

```bash
# CLI（本機，gitignored）
python generate_report.py --union 海星社
python generate_report.py --union 3403
python generate_report.py --union 百成 --region 雲林   # 同名社須指定區域
python generate_report.py --union 海星社 --ai          # 附帶 AI 分析

# Streamlit
streamlit run app_report.py    # 本機（讀取 ../下載工具/ 檔案）
streamlit run app.py           # 雲端模式（上傳檔案）

# 驗證（本機，僅 3403 海星社，gitignored）
python verify_data.py          # 10 項數據交叉驗證
python check_html.py           # HTML 值檢查
```

## 模組流向

```
report_config.py   → 設定、THRESHOLDS、GEMINI_MODEL、轉換工具
report_data.py     → load_data(), extract_union_data() → d dict
report_charts.py   → generate_all_charts(d) → charts dict
report_ai.py       → analyze_with_gemini(d, api_key) → str | None
report_html.py     → build_report(d, charts, ai_analysis=None) → HTML
```

## 百分比清洗（`_clean_excel` in `report_data.py`）

| 欄位 | Excel 儲存 | 清洗規則 |
|------|-----------|----------|
| 儲蓄率 | `105.3`（= 105.3%） | `/100` if `abs(x)>1.0` |
| 開支比 | `99.5`（= 99.5%） | `/100` if `abs(x)>5.0` |
| 逾放比 | `0.054` | 不做除法 |
| 貸放比 | `0.24` | 不做除法 |

Excel 欄位名稱錯位（iloc[5]=貸放比, iloc[6]=儲蓄率），新系統用名稱讀取已避開。

## 關鍵坑

- **合併鍵用社號**，不用社名（防更名）
- **民國年月** 5 碼 `11504` = 2026-04，`convert_minguo_date()` 轉 datetime
- **CSV 讀取**強制 `encoding='utf-8-sig'`
- **`st.expander` 禁止使用**（父層 UI 規範，高齡長輩友善）
- **門檻值集中於 `THRESHOLDS` dict**（`report_config.py`），勿散落各檔案
- **無 pyproject.toml**，無 lint/typecheck/formatter
- **33 社**：雲林 13 社（3201-3214 缺 3209）、嘉義 20 社（詳 `../AGENTS.md`）
- **驗證腳本全硬編碼 `3403`**，不可套用他社
- **`html` 變數名衝突**：`report_html.py` 用 `from html import escape as html_escape`，避免與 f-string 區域變數 `html` 衝突

## AI 顧問分析（Gemini）

`report_ai.py` 串接 Gemini 2.5 Flash-Lite，產出儲互社財務顧問分析。
- 依賴環境變數 `GEMINI_API_KEY`（或 Streamlit Cloud `st.secrets`）
- Streamlit 入口：勾選「啟用儲互社 AI 顧問分析」
- CLI 入口：`--ai` flag
- 失敗不回傳錯誤，區塊不顯示
- 套件：`google-genai`（新版，非已棄用的 `google-generativeai`）
- 免費額度：1500 RPD，單社 1 次呼叫綽綽有餘

## 風險診斷（2/5 原則）

```python
# extract_union_data()，滿足 ≥2 項為「重點輔導」：
c1 = 開支比連兩年 >1.0
c2 = 貸放比 <0.1
c3 = 逾放比 >0.5 and 逾期貸款增加
c4 = 社員連三年衰退（M0<M1<M2<M3）
c5 = 股金連三年衰退（S0<S1<S2<S3）
```

## 部署

GitHub: `rock903400-byte/report-generator` → Streamlit Cloud（入口 `app.py`）
網址：https://rock903400-byte-report-generator-app-8hwvwm.streamlit.app/

## 參考

- `../AGENTS.md` — 全工作區架構、社號速查表
- `../下載工具/AGENTS.md` — 百分比清洗原始邏輯

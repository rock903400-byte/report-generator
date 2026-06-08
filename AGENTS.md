# AGENTS.md — 報告工具

## Git 追蹤（20 檔上 GitHub / Streamlit Cloud）

```
app.py  report_config.py  report_data.py  report_charts.py
report_html.py  report_ai.py  requirements.txt  AGENTS.md
common/*.py  (7 檔: __init__, classifier, cleaning, constants, dates, thresholds, utils)
templates/report.html
tests/__init__.py  tests/conftest.py
tests/test_report_config.py  tests/test_report_data.py
```

**.gitignore**（僅本機）：`generate_report.py` `app_report.py` `app_cloud.py` `generate_dabang_report.py` `verify_data.py` `verify_full.py` `check_html.py` `output/` `.streamlit/secrets.toml` `*.txt` `__pycache__/`

改 `app.py` / `report_*.py` / `common/` / `templates/report.html` → `git add && git push` → Streamlit Cloud 1–3 min 自動部署。

## Entry Points

| 系統 | 入口 | 用途 |
|------|------|------|
| 雲端 | `app.py` | Streamlit Cloud，上傳檔案 + 簡易密碼閘門 (`st.secrets.APP_PASSWORD`) |
| 本機 Streamlit | `app_report.py` | 讀 `../下載工具/` 檔，輸出到 `output/` |
| CLI | `generate_report.py` | 批次產出至 `output/` |

所有入口走同一 `report_*.py` 鏈。

## Module Flow

```
common/          → 共用工具（dates/utils/thresholds/cleaning/classifier/constants）
report_config.py → config, REGIONS, THRESHOLDS, GEMINI_MODEL, fmt/fmt_pct
report_data.py   → load_data*() → (df_m, df_l, df_csv), extract_union_data() → d dict
report_charts.py → generate_all_charts(d) → charts dict (Plotly HTML divs)
report_ai.py     → analyze_with_gemini(d, api_key) → str | None
report_html.py   → build_report(d, charts, ai_analysis)  → HTML str
                   (Jinja2: templates/report.html)
```

## CLI

```bash
python generate_report.py --union 海星社         # 依社名
python generate_report.py --union 3403            # 依社號
python generate_report.py --union 百成 --region 雲林  # 同名社需指定區域
python generate_report.py --union 海星社 --ai     # 附 AI 顧問分析
```

## Tests（追蹤）

```bash
python -m pytest tests/ -v            # 17 項（report_config + report_data）
```

`tests/conftest.py` mock `streamlit` module before imports（`sys.modules["streamlit"] = MagicMock()`）。

No pyproject.toml, no lint/typecheck/formatter.

## 32 社

- **雲林** 13 社：3201–3214（缺 3209）
- **嘉義** 19 社：3301,3305,3307, 3401–3417（缺 3405）
- 完整對照表在 `report_config.py:REGIONS`，合併鍵**用社號**（非社名，防更名）。

## Data Cleaning

`common/cleaning.py:defensive_clean_series()` 處理 Excel 百分比異常儲存：

| 欄位 | 規則 |
|------|------|
| 儲蓄率 | `/100` if `abs(x)>1.0` |
| 開支比 | `/100` if `abs(x)>5.0` |
| 逾放比、提撥率 | 不除 |
| 貸放比 | `/100` if `abs(x)>1.0`（但在 `report_data.py:_clean_excel` 先用 `pd.to_numeric` 處理後不再重除） |

Excel 舊版欄位錯位（iloc[5]=貸放比, iloc[6]=儲蓄率），新系統用欄位名稱讀取已避開。

## Risk Diagnosis

`common/classifier.py:classify()` 回傳 `(status, reason_text)`，五種狀態：

| 條件 | status |
|------|--------|
| ≥2 項觸發（c1–c5） | 🚨 特別關懷 |
| 貸放比>90% 且股金衰退 | ⚠️ 流動性緊繃 |
| 貸放比<30% 且逾放安全 | 💤 資金閒置 |
| 社員/股金正成長、貸放比40–80%、逾放<2% | ✅ 穩健模範 |
| 其他 | 📊 一般狀態 |

觸發規則 (c1–c5)：`R0/R1>1.0`(連兩年虧損) / `eLoan<0.1`(貸放比過低) / `eOvd>0.5 & O0>O1`(高逾放惡化) / `M0<M1<M2<M3`(人數連三衰退) / `S0<S1<S2<S3`(股金連三衰退)。

## AI Advisory（Gemini）

`report_ai.py` → `google-genai`（新版 SDK，非已棄用 `google-generativeai`）。

- Model: `report_config.py:GEMINI_MODEL`（目前 `gemini-2.5-flash`），改此處 HTML footer 自動跟
- `max_output_tokens=600`（不是 4096）
- API key: 環境變數 `GEMINI_API_KEY` 或 Streamlit Cloud `st.secrets.GEMINI_API_KEY`
- 失敗回傳 `None`，區塊不顯示
- `report_html.py:_md_to_html()` 將 Gemini markdown 轉 HTML（支援 `**粗體**` 列表、`# ` 標題、`- ` 無序/`1. ` 有序列表）
- `report_html.py:_is_ai_truncated()` 檢測截斷（缺少「建議」或結尾 markdown 不完整），截斷時顯示警告而非殘缺內容

## Key Pitfalls

- **民國年月** 5 碼 `11504`=2026-04：`common/dates.py:convert_minguo_date()` 轉 datetime
- **CSV** 強制 `encoding='utf-8-sig'`，缺少欄位時跳過不中斷流程
- **`html` 變數衝突**：`report_html.py` `from html import escape as html_escape`（非標準庫 `html` 模組）
- **`st.expander` 禁用**（高齡友善 UI 規範）
- **民國年 4 碼** `5104` 亦由 `convert_minguo_date()` 支援（前 2 碼 +1911）
- **Plotly chart 輸出**：`to_html(full_html=False, include_plotlyjs=False)`，JS 由模板統一載入 CDN

## Dependencies（`requirements.txt`）

```
pandas>=2.0  plotly>=5.18  streamlit>=1.28  openpyxl>=3.1
google-genai  jinja2>=3.1  pytest>=9.0
```

## 外部參考

- `../AGENTS.md` — 全工作區架構、社號速查表
- `../下載工具/AGENTS.md` — 百分比清洗原始邏輯

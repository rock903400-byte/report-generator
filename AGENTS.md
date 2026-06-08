# AGENTS.md — 報告工具

## Git 追蹤（重要）

**僅 8 檔上 GitHub / Streamlit Cloud：**
`app.py` `report_config.py` `report_data.py` `report_charts.py` `report_html.py` `report_ai.py` `requirements.txt` `AGENTS.md`

**僅本機存在（gitignored）：**
`generate_report.py` `app_report.py` `app_cloud.py` `generate_dabang_report.py` `verify_data.py` `verify_full.py` `check_html.py` `output/` `.streamlit/secrets.toml`

改 `report_*.py` 或 `app.py` → `git add && git push` → Streamlit Cloud 1–3 min 自動部署。

## Entry Points

| 系統 | 入口 | 用途 |
|------|------|------|
| 雲端 | `app.py` | Streamlit Cloud，上傳檔案 |
| 本機 Streamlit | `app_report.py` | 讀 `../下載工具/` 檔 |
| CLI | `generate_report.py` | 指令列批次產出 |

所有入口走同一 `report_*.py` 鏈。

## Module Flow

```
report_config.py   → config, REGIONS, THRESHOLDS, GEMINI_MODEL, fmt utils
report_data.py     → load_data(), extract_union_data() → d dict
report_charts.py   → generate_all_charts(d) → charts dict (Plotly HTML divs)
report_ai.py       → analyze_with_gemini(d, api_key) → str | None
report_html.py     → build_report(d, charts, ai_analysis=None) → HTML str
```

## CLI Commands

```bash
python generate_report.py --union 海星社        # 依社名
python generate_report.py --union 3403           # 依社號
python generate_report.py --union 百成 --region 雲林  # 同名社須指定區域
python generate_report.py --union 海星社 --ai    # 附 AI 顧問分析
```

## 單元測試（pytest，追蹤）

```bash
python -m pytest tests/ -v   # 17 項測試（report_config + report_data）
```

`tests/conftest.py` mock `streamlit` module before imports.
測試 cover: REGIONS 結構、find_union、THRESHOLDS 鍵、_clean_excel、
load_data_from_bytes（含錯誤 sheet、CSV）、extract_union_data、compute_ovd_stats。

## Verify（僅本機，gitignored，硬編碼 3403 海星社）

```bash
python verify_data.py   # 10 項 CSV 科目交叉驗證
python check_html.py    # HTML 值一致性檢查
```

No pyproject.toml, no lint/typecheck/formatter.

## 32 社

- **雲林** 13 社：3201–3214（缺 3209）
- **嘉義** 19 社：3301,3305,3307, 3401–3417（缺 3405）
- 完整對照表在 `report_config.py:REGIONS`
- 合併鍵**用社號**，不用社名（防更名）

## Data Cleaning（`report_data.py:_clean_excel`）

| 欄位 | Excel 儲存 | 規則 |
|------|-----------|------|
| 儲蓄率 | `105.3`（=105.3%） | `/100` if `abs(x)>1.0` |
| 開支比 | `99.5`（=99.5%） | `/100` if `abs(x)>5.0` |
| 逾放比 | `0.054` | 不除 |
| 貸放比 | `0.24` | 不除 |

Excel 欄位名稱錯位（iloc[5]=貸放比, iloc[6]=儲蓄率），新系統用名稱讀，已避開。

## Key Pitfalls

- **民國年月** 5 碼 `11504`=2026-04，`convert_minguo_date()` 轉 datetime
- **CSV** 強制 `encoding='utf-8-sig'`
- **`st.expander` 禁用**（高齡友善 UI 規範）
- **`THRESHOLDS` dict** 集中在 `report_config.py`，勿散落
- **`html` 變數衝突**：`report_html.py` `from html import escape as html_escape`
- **`report_html.py`** 從 `report_config` 引入 `GEMINI_MODEL` 動態顯示在 AI 區塊 footer

## AI Advisory（Gemini）

`report_ai.py` 串接 Gemini API，目前使用 `gemini-2.5-flash`（設定於 `report_config.py:GEMINI_MODEL`）。
- API key：環境變數 `GEMINI_API_KEY` 或 Streamlit Cloud `st.secrets.GEMINI_API_KEY`
- `max_output_tokens=4096`
- 套件：`google-genai`（新版 SDK，非已棄用 `google-generativeai`）
- 免費額度 ~1500 RPD，33 社一次跑也才 33 次呼叫
- 失敗不回傳錯誤，區塊不顯示
- Streamlit 入口：勾選「啟用儲互社 AI 顧問分析」
- CLI 入口：`--ai` flag
- 更換模型只需改 `report_config.py` `GEMINI_MODEL`，HTML footer 自動跟

## Risk Diagnosis（2/5 原則）

`extract_union_data()` 中，滿足 ≥2 項為「重點輔導」：

```python
c1 = 開支比連兩年 > 1.0
c2 = 貸放比 < 0.1
c3 = 逾放比 > 0.5 and 逾期貸款增加
c4 = 社員連三年衰退 (M0<M1<M2<M3)
c5 = 股金連三年衰退 (S0<S1<S2<S3)
```

## Dependencies（`requirements.txt`）

```
pandas>=2.0  plotly>=5.18  streamlit>=1.28  openpyxl>=3.1  google-genai  pytest>=9.0
```

## Deployment

GitHub: `rock903400-byte/report-generator` → Streamlit Cloud（入口 `app.py`）
URL: https://rock903400-byte-report-generator-app-8hwvwm.streamlit.app/

## 身分驗證（Streamlit Cloud 選用）

`app.py` 支援簡易密碼保護：
- 在 `.streamlit/secrets.toml` 設 `APP_PASSWORD` → 啟用密碼閘門
- 無該設定 → 跳過驗證（向後相容）
- 僅作用於 `app.py`（雲端），不影響本機入口

## 錯誤訊息友善化

`report_data.py:load_data_from_bytes()` 現在對常見錯誤有明確提示：
| 情境 | 使用者看到 |
|------|-----------|
| Excel 無法開啟 | 「無法讀取 Excel 檔案，請確認上傳的是正確的資料庫.xlsx」 |
| 缺少工作表 | 「Excel 缺少工作表「放款及逾期放款」（應為 […]）」 |
| 缺少必要欄位 | 「社務資料工作表缺少欄位：貸放比, 儲蓄率」 |
| 年月格式錯誤 | 「清洗後社務資料無有效資料，請檢查年月格式」 |
| CSV 缺少欄位 | 跳過 CSV，不中斷流程 |

## 參考外部檔案

- `../AGENTS.md` — 全工作區架構、社號速查表
- `../下載工具/AGENTS.md` — 百分比清洗原始邏輯

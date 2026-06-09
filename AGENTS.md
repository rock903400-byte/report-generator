# AGENTS.md — 報告工具

## Git 追蹤（上 GitHub / Streamlit Cloud）

```
app.py  report_config.py  report_data.py  report_charts.py
report_html.py  report_ai.py  requirements.txt  AGENTS.md
pyproject.toml  .github/workflows/test.yml
common/*.py  (7 檔: __init__, classifier, cleaning, constants, dates, thresholds, utils)
templates/report.html
tests/__init__.py  tests/conftest.py
tests/test_report_config.py  tests/test_report_data.py
tests/test_*.py  (14 新增測試檔)
```

**`.gitignore`**（僅本機）：`generate_report.py` `app_report.py` `app_cloud.py` `generate_dabang_report.py` `verify_data.py` `verify_full.py` `check_html.py` `output/` `.streamlit/secrets.toml` `*.txt` `__pycache__/`

改 `app.py` / `report_*.py` / `common/` / `templates/report.html` → `git add && git push` → Streamlit Cloud 1–3 min 自動部署。

## Module Flow

```
common/          → 共用工具（dates/utils/thresholds/cleaning/classifier/constants）
report_config.py → config, REGIONS, GEMINI_MODEL, fmt/fmt_pct
report_data.py   → load_data*() → (df_m, df_l, df_csv), extract_union_data() → d dict
report_charts.py → generate_all_charts(d) → charts dict (Plotly HTML divs)
report_ai.py     → analyze_with_gemini(d, api_key) → (str | None, str | None)
report_html.py   → build_report(d, charts, ai_analysis)  → HTML str (Jinja2: templates/report.html)
```

## Tests

```bash
python -m pytest tests/ -v                    # 235 tests, 96% coverage
python -m pytest tests/ --cov --cov-fail-under=80  # CI gate
python -m pytest tests/test_charts.py -v      # 單檔
python -m pytest tests/test_classifier.py::TestClassifySpecialCare -v  # 單類
```

**Key testing quirks:**
- `conftest.py` mocks `streamlit` at module level (`sys.modules["streamlit"] = MagicMock()`) — required before any import that touches streamlit
- `st.session_state` uses custom `_SessionState(dict)` for both `in` and attribute access
- `st.columns` returns `(MagicMock(), MagicMock())` for tuple unpacking
- `app.py` smoke test (`test_app_smoke.py`) checks syntax + import resolution — does **not** execute module-level code (too much Streamlit interaction)
- Plotly chart tests (`test_charts.py`) check HTML structure, not Chinese text (Plotly escapes Unicode in JSON)
- Playwright tests (`test_html_playwright.py`) need `playwright install chromium` before first run

## 32 社

- 雲林 13 社（3201–3214 缺 3209）、嘉義 19 社（3301,3305,3307, 3401–3417 缺 3405）
- 合併鍵用**社號**（非社名，防更名）；對照表在 `report_config.py:REGIONS`

## Data Cleaning

`common/cleaning.py:defensive_clean_series()`:

| 欄位 | 規則 |
|------|------|
| 儲蓄率 | `/100` if `abs(x)>1.0` |
| 開支比 | `/100` if `abs(x)>5.0` |
| 逾放比、提撥率 | 不除 |
| 貸放比 | `/100` if `abs(x)>1.0`（`_clean_excel` 先用 `pd.to_numeric` 後不再重除） |

## Risk Diagnosis

`classify()` 五狀態優先序：特別關懷(≥2條件) → 流動性緊繃(貸放比>90%+股金衰退) → 資金閒置(貸放比<30%+逾放安全) → 穩健模範(正向指標) → 一般狀態(其他)。

5 條件(c1–c5)：`R0/R1>1.0`(連兩年虧損) / `eLoan<0.1`(貸放比過低) / `eOvd>0.5 & O0>O1`(高逾放惡化) / `M0<M1<M2<M3`(人數連三衰退) / `S0<S1<S2<S3`(股金連三衰退)。

## AI Advisory（Gemini）

- SDK: `google-genai`（新版），非已棄用之 `google-generativeai`
- Model: `GEMINI_MODEL` in `report_config.py`（改此處 → HTML footer 自動跟）
- `max_output_tokens=2048`
- API key: env `GEMINI_API_KEY` 或 `st.secrets.GEMINI_API_KEY`；失敗回傳 `(None, error_msg)`
- `analyze_with_gemini()` 回傳 `(str | None, str | None)`：`(分析結果, 錯誤訊息)`
- `_md_to_html()` 轉 Gemini markdown（`**粗體**`、`#`、`-`/`1.` 列表，**不支援表格**）
- `_is_ai_truncated()` 檢查截斷（以 `**` / `*` / `-` / `：` 結尾 → 顯示警告）

### Prompt 結構

語氣：專業、客觀、簡潔，像寫給理事會的內部報告。總字數 600 字內。

1. **財務健康評分卡**（巢狀列表格式）
   - 成長性：3Y 社員成長 >10% → 8-10 分；0-10% → 5-7 分；<0% → 1-4 分
   - 資產品質：逾放比 <1% → 9-10 分；1-2% → 6-8 分；2-5% → 3-5 分；>5% → 1-2 分
   - 獲利能力：開支比 <90% → 8-10 分；90-100% → 5-7 分；>100% → 1-4 分
   - 流動性：貸放比 40-80% → 8-10 分；30-40% 或 80-90% → 5-7 分；<30% 或 >90% → 1-4 分
   - 總體評分：四維度平均，資產品質權重 1.5 倍

2. **風險評估**（按嚴重程度排序，標註高/中/低）

3. **量化改善建議**（含公式、目標、預期效益、時間框架）

4. **亮點**（若有顯著優勢）

邊界情況：資料不足 3 年時以實際可用年數評估並註明。

## Key Pitfalls

- **民國年月** 5 碼 `11504`=2026-04、4 碼 `5104`=1962-04（`convert_minguo_date()` 處理）
- **CSV** 強制 `encoding='utf-8-sig'`，缺少欄位時跳過不中斷流程
- **`html` 變數衝突**：`report_html.py` 用 `from html import escape as html_escape`（非標準庫 `html`）
- **Plotly chart 輸出**：`to_html(full_html=False, include_plotlyjs=False)`，JS 由模板統一載入 CDN
- **`.coverage` / `htmlcov/`** 不在 `.gitignore` — 留意勿 commit

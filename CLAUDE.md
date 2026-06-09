# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 常用指令

```bash
# 測試（235 項）
python -m pytest tests/ -v
python -m pytest tests/test_charts.py -v                           # 單檔
python -m pytest tests/test_classifier.py::TestClassifySpecialCare -v  # 單類

# 品質檢查（順序：format → lint → type-check）
python -m black . --line-length 100
python -m ruff check .
python -m mypy report_config.py report_data.py report_charts.py report_html.py report_ai.py common/ --ignore-missing-imports --no-strict-optional

# 本機 Streamlit
streamlit run app.py          # 雲端版（上傳檔案 + APP_PASSWORD）
streamlit run app_report.py   # 本機版（讀 ../下載工具/ 檔）
```

**部署**：改任何 git-tracked 檔 → `git push` → Streamlit Cloud 自動部署（1–3 分鐘）。

---

## 架構

### 資料流

```
資料庫.xlsx + exported_data.csv
        ↓
report_data.py   load_data_from_bytes() → (df_m, df_l, df_csv)
                 extract_union_data()   → d dict（單一社的完整資料包）
        ↓
report_charts.py  generate_all_charts(d) → charts dict（Plotly HTML divs）
report_ai.py      analyze_with_gemini(d, api_key) → (str|None, str|None)
report_html.py    build_report(d, charts, ai_analysis) → HTML str
                  （Jinja2 模板：templates/report.html）
```

所有下游模組（charts / html / ai）只吃 `d` dict，不直接讀檔案。

### 入口點

| 檔案 | 用途 |
|------|------|
| `app.py` | **Git 追蹤，Streamlit Cloud 部署版**，上傳檔案 + `APP_PASSWORD` 閘門 |
| `app_report.py` | 本機，讀 `../下載工具/` 固定路徑（`.gitignore`） |
| `generate_report.py` | CLI 批次，`--union 社名/社號 [--region 區域] [--ai]`（`.gitignore`） |

### `d` dict 結構（`extract_union_data` 輸出）

| 鍵群 | 說明 |
|------|------|
| `s_no`, `s_name`, `max_d`, `min_d` | 基本資訊 |
| `T0`–`T3`, `T_12M` | 時間基準點（T0=最近年底 12月、T1–T3往前各一年） |
| `df_m`, `df_l`, `df_csv` | 此社完整月份序列（已依社號過濾） |
| `M0`–`M3`, `S0`–`S3` | 社員數/股金各年底快照 |
| `R0`, `R1` | 開支比（年底，R0>1.0 表虧損） |
| `O0`, `O1` | 逾期貸款金額（年底） |
| `eOvd`, `eLoan`, `eRate`, `eProv` | 最新年底各率 |
| `curr_M`, `curr_S` | 最新月份社員數/股金 |
| `memG_curr`, `shrG_curr` | 12M YoY 成長率（相對 T0） |
| `status`, `status_color`, `reason_text` | 風險診斷結果 |
| `notes`, `risk_count` | 觸發條目列表與觸發條件數（0–5） |

### `common/` 共用模組

| 模組 | 主要功能 |
|------|---------|
| `dates.py` | `convert_minguo_date()`（5碼民國→datetime）、`get_value(df, col, date)` |
| `cleaning.py` | `defensive_clean_series()`：儲蓄率/貸放比 >1 ÷100、開支比 >5 ÷100；逾放比/提撥率不動 |
| `classifier.py` | `classify(p, thresholds)` → (status, reason_text)，五狀態判定 |
| `thresholds.py` | `DEFAULT_THRESHOLDS`、`load_thresholds(secrets)` |
| `utils.py` | `safe_div()`、`format_large_number()`（≥億→「億元」）、`fmt_pct()` |

`report_config.py` re-exports `convert_minguo_date`, `get_value`, `safe_div`, `fmt`, `fmt_pct`，其他模組從 `report_config` import，不直接從 `common` import。

---

## 社別對照表

105 社，對照表在 `report_config.py:REGIONS`，**合併鍵用社號（非社名）**：

- 雲林 13 社（32xx）、嘉義 19 社（33xx/34xx）
- 台中 19 社（22xx/23xx）、南投 34 社（24xx）、彰化 20 社（31xx）

`find_union(keyword)` 接受社名或社號字串，回傳 `(社號, 社名, 區域)` 或 `None`。

---

## 風險診斷邏輯

`common/classifier.py` 優先序（第一匹配即停）：

1. `≥2 項觸發` → 🚨 特別關懷
2. `eLoan>0.9 且 shrG<0` → ⚠️ 流動性緊繃
3. `eLoan<0.3 且 eOvd<safe_line` → 💤 資金閒置
4. `memG≥0 且 shrG≥0 且 0.4≤eLoan≤0.8 且 eOvd<safe_line` → ✅ 穩健模範
5. 其他 → 📊 一般狀態

五條件（c1–c5）：`R0/R1>1.0`（連兩年虧損）/ `eLoan<0.1` / `eOvd>0.5 且 O0>O1` / 人數連三衰退 / 股金連三衰退。

---

## 關鍵注意事項

- **民國年月**：5 碼 `11504`=2026-04；4 碼舊格式由 `convert_minguo_date()` 處理。
- **CSV encoding**：強制 `utf-8-sig`；缺欄位時跳過不中斷。
- **Plotly 輸出**：`to_html(full_html=False, include_plotlyjs=False)`，JS 由 `templates/report.html` 從 CDN 載入；所有圖表禁縮放（`dragmode=False`, `fixedrange=True`）。
- **`html` 變數衝突**：`report_html.py` 用 `from html import escape as html_escape`。
- **`tests/conftest.py`**：在任何 import 前注入 `sys.modules["streamlit"] = MagicMock()`；`st.session_state` 用自訂 `_SessionState(dict)` 支援屬性存取。
- **Playwright 測試**：初次執行需 `playwright install chromium`。
- **年化放款利率計算**：`131x` 放款餘額須先 `.groupby(["年","年月"]).sum()` 取月度合計，再 `.groupby(level=0).mean()` 取年均，否則多子科目時分母偏小導致利率虛高。
- **`secrets.toml`** 在 `.gitignore`；本機複製 `secrets_template.toml`；Streamlit Cloud 直接在 Dashboard 設定。
- **E402 noqa**：`report_config.py` 和 `report_data.py` 因 `sys.path` 前置操作，`import` 行需 `# noqa: E402`；re-export import 需 `# noqa: F401`。
- **`.coverage` / `htmlcov/`** 不在 `.gitignore`，勿 commit。

# AGENTS.md — 報告工具

## 兩套子系統

| 系統 | 組成 | 備註 |
|------|------|------|
| **Plotly 新系統** | `report_config.py` `report_data.py` `report_charts.py` `report_html.py` + `generate_report.py` / `app_report.py` / `app_cloud.py` | 支援 33 社，可改 |
| **舊靜態報告** | `generate_dabang_report.py` `verify_data.py` `verify_full.py` `check_html.py` | **勿修改**（AGENTS.md 已標示） |

## 常用指令

```bash
# Plotly 新系統（輸出到 output/）
python generate_report.py --union 海星社          # 依社名
python generate_report.py --union 3403             # 依社號
python generate_report.py --union 百成 --region 雲林  # 同名社須指定區域

# Streamlit 入口
streamlit run app_report.py    # 本機版（讀 ../下載工具/）
streamlit run app_cloud.py     # 雲端版（需上傳檔案）

# 舊驗證（僅 3403 海星社，勿改）
python verify_data.py
python check_html.py
```

**注意：** `generate_dabang_report.py` 產出在當前目錄（非 `output/`），因內嵌程式碼而非使用 `report_*.py` 模組。

## 百分比清洗（`_clean_excel` in `report_data.py`）

| 欄位 | Excel 儲存格式 | 清洗後 |
|------|---------------|--------|
| 儲蓄率 | `105.3`（表 105.3%） | `/100` if `abs(x)>1.0` → `1.053` |
| 開支比 | `99.5`（表 99.5%） | `/100` if `abs(x)>5.0` → `0.995` |
| 逾放比 | `0.054`（已小數） | 不做除法 |
| 貸放比 | `0.24`（已小數） | 不做除法 |

Excel 欄位名稱錯位（iloc[5]=貸放比, iloc[6]=儲蓄率），新系統用欄位名稱讀取已避開。

## 關鍵坑

- **合併鍵用社號**，不用社名（防更名）
- **民國年月**：5 碼 `11504` = 2026-04，`convert_minguo_date()` 轉 datetime
- **33 社**：雲林 13 社（3201-3214 缺 3209）、嘉義 20 社
- **無 pyproject.toml**，無 lint/typecheck/formatter
- CSV 讀取強制 `encoding='utf-8-sig'`
- `st.expander` 禁止使用（父層 UI 規範：高齡長輩友善）
- 門檻值集中於 `report_config.py` `THRESHOLDS` dict，勿硬編碼於其他檔案
- 驗證腳本全硬編碼 `3403`，無法直接套用他社

## 模組流向

```
report_config.py   →  THRESHOLDS, convert_minguo_date, safe_div, fmt, get_value
report_data.py     →  load_data(), extract_union_data() → d dict
report_charts.py   →  generate_all_charts(d) → charts dict（Plotly div + 資產負債表 HTML）
report_html.py     →  build_report(d, charts) → HTML 字串
generate_report.py →  CLI: parse args → load → extract → chart → build → output/
```

## 風險診斷（2/5 原則，`extract_union_data` 內）

```python
# 滿足 ≥2 項為「重點輔導」：
c1 = 開支比連兩年 >THRESHOLDS["high_risk_income_ratio"]  # 1.0
c2 = 貸放比 <THRESHOLDS["high_risk_loan_ratio"]           # 0.1
c3 = 逾放比 >THRESHOLDS["high_risk_ovd_ratio"] and 逾期貸款增加  # 0.5
c4 = 社員連三年衰退（M0<M1<M2<M3）
c5 = 股金連三年衰退（S0<S1<S2<S3）
```

門檻值請改 `THRESHOLDS` dict，勿散落各檔案。

## 參考

- `../AGENTS.md` — 全工作區概觀、社號速查表
- `../下載工具/AGENTS.md` — 百分比清洗原始邏輯

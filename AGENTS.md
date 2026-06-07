# AGENTS.md — 報告工具

## 兩套子系統

| 系統 | 組成 | 備註 |
|------|------|------|
| **Plotly 新系統** | `report_config.py` `report_data.py` `report_charts.py` `report_html.py` + `generate_report.py` / `app_report.py` / `app.py` | 支援 33 社，可改 |
| **舊靜態報告** | `generate_dabang_report.py` `verify_data.py` `verify_full.py` `check_html.py` | **勿修改** |

`report_*.py` 為核心模組，入口有三種：`generate_report.py`（CLI）、`app_report.py`（本機 Streamlit）、`app.py`（雲端 Streamlit）。

## 常用指令

```bash
# Plotly 新系統
python generate_report.py --union 海星社          # 依社名
python generate_report.py --union 3403             # 依社號
python generate_report.py --union 百成 --region 雲林  # 同名社須指定區域

# Streamlit
streamlit run app_report.py    # 本機（讀取 ../下載工具/ 檔案）
streamlit run app.py           # 雲端模式（上傳檔案）
streamlit run app_cloud.py     # 同上，本地用

# 舊驗證（僅 3403 海星社，勿改）
python verify_data.py
python check_html.py
```

`generate_dabang_report.py` 內嵌了整套 `report_*.py` 邏輯，產出在當前目錄而非 `output/`。

## 百分比清洗（`_clean_excel` in `report_data.py`）

| 欄位 | Excel 儲存 | 清洗 |
|------|-----------|------|
| 儲蓄率 | `105.3`（表 105.3%） | `/100` if `abs(x)>1.0` |
| 開支比 | `99.5`（表 99.5%） | `/100` if `abs(x)>5.0` |
| 逾放比 | `0.054`（小數） | 不做除法 |
| 貸放比 | `0.24`（小數） | 不做除法 |

Excel 欄位名稱錯位（iloc[5]=貸放比, iloc[6]=儲蓄率），新系統用名稱讀取已避開。

## 關鍵坑

- **合併鍵用社號**，不用社名（防更名）
- **民國年月** 5 碼 `11504` = 2026-04，`convert_minguo_date()` 轉 datetime
- **CSV 讀取**強制 `encoding='utf-8-sig'`
- **`st.expander` 禁止使用**（父層 UI 規範，高齡長輩友善）
- **門檻值集中於 `THRESHOLDS` dict**（`report_config.py`），勿散落各檔案
- **無 pyproject.toml**，無 lint/typecheck/formatter
- **33 社**：雲林 13 社（3201-3214 缺 3209）、嘉義 20 社（詳 `../AGENTS.md` 速查表）
- **驗證腳本全硬編碼 `3403`**，不可套用他社

## 模組流向

```
report_config.py   → 設定、THRESHOLDS、轉換工具
report_data.py     → load_data(), extract_union_data() → d dict
report_charts.py   → generate_all_charts(d) → charts dict
report_html.py     → build_report(d, charts) → HTML
generate_report.py → CLI 入口：parse → load → extract → chart → build → output/
```

`app_report.py` / `app.py` 走相同鏈。`compute_ovd_stats()` 和 `make_balance_sheet_html()` 已有空 DataFrame guard。

## 風險診斷（2/5 原則）

```python
# extract_union_data()，滿足 ≥2 項為「重點輔導」：
c1 = 開支比連兩年 >THRESHOLDS["high_risk_income_ratio"]   # 1.0
c2 = 貸放比 <THRESHOLDS["high_risk_loan_ratio"]            # 0.1
c3 = 逾放比 >THRESHOLDS["high_risk_ovd_ratio"] and 逾期貸款增加  # 0.5
c4 = 社員連三年衰退（M0<M1<M2<M3）
c5 = 股金連三年衰退（S0<S1<S2<S3）
```

## 部署

GitHub: `rock903400-byte/report-generator` → Streamlit Cloud 自動佈署（入口 `app.py`）。`git push` 後 1–3 分鐘生效。

網址：https://rock903400-byte-report-generator-app-8hwvwm.streamlit.app/

## 參考

- `../AGENTS.md` — 全工作區架構、社號速查表
- `../下載工具/AGENTS.md` — 百分比清洗原始邏輯

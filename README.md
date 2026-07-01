# report-generator

> AI 報表產生器 — 自動化財務分析與營運報告生成系統

## 功能特色

- **AI 報告撰寫**：自動整合 AI 模型進行財務與營運分析，並生成文字段落。
- **統計圖表繪製**：自動產出數據視覺化圖表，並支援貝福法則 (Benford's Law) 的首位數頻率分佈檢驗以揪出潛在舞弊。
- **多格式匯出**：支援將產出的報告導出為 PDF 與 HTML 格式。

## 技術棧

- **Frontend / UI**: Streamlit (Python)
- **Backend**: Python (report_ai.py, report_charts.py)
- **Testing / CI**: pytest, GitHub Actions

## 快速開始

### 1. 安裝環境需求
```bash
pip install -r requirements.txt
```

### 2. 啟動 Streamlit 服務
```bash
streamlit run app.py
```

## 專案結構

```text
/
├── app.py              # Streamlit 網頁主入口
├── report_ai.py        # AI 核心分析與生成模組
├── report_charts.py    # Plotly/Matplotlib 圖表繪製與貝福法則分析
├── report_data.py      # 財務數據載入與資料清理
├── report_export.py    # 匯出為 HTML / PDF 的格式轉換
├── tests/              # pytest 單元測試目錄
└── .github/            # GitHub Actions 流程配置
```

## License

MIT

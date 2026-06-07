#!/usr/bin/env python
"""
Streamlit Cloud 版：理事會報告產生器
使用者上傳 Excel + CSV → 選擇儲互社 → 產出 HTML 報告 → 下載
"""
import os
import sys
import io
import pandas as pd
import streamlit as st
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from report_config import REGIONS
from report_data import load_data_from_bytes, extract_union_data
from report_charts import generate_all_charts
from report_html import build_report
from report_ai import analyze_with_gemini

st.set_page_config(
    page_title="理事會報告產生器",
    page_icon="📊",
    layout="centered",
)

st.title("📊 理事會財務分析報告產生器")
st.markdown("上傳資料檔案，選擇儲互社，一鍵產出 HTML 報告。")

# ── 檔案上傳 ──────────────────────────────────────────────────
st.markdown("### 📂 上傳資料檔案")
col1, col2 = st.columns(2)
with col1:
    xls_file = st.file_uploader(
        "資料庫.xlsx（必要）",
        type=["xlsx"],
        help="從「下載工具」下載的資料庫 Excel 檔案",
    )
with col2:
    csv_file = st.file_uploader(
        "exported_data.csv（選填）",
        type=["csv"],
        help="PR019 財務科目明細，無 CSV 則跳過資產負債表等財務分析",
    )

if xls_file is None:
    st.info("請先上傳「資料庫.xlsx」以開始使用。")
    st.markdown("### ℹ️ 使用說明")
    st.markdown("""
    1. 先從「下載工具」下載 **資料庫.xlsx** 和 **exported_data.csv**
    2. 將兩個檔案上傳到此頁面
    3. 選擇儲互社
    4. 按「產生報告」下載 HTML
    """)
    st.stop()

# ── 載入資料 ──────────────────────────────────────────────────
with st.spinner("載入資料中…"):
    try:
        excel_bytes = xls_file.read()
        csv_bytes = csv_file.read() if csv_file is not None else None
        df_m, df_l, df_csv = load_data_from_bytes(excel_bytes, csv_bytes)
        has_csv = csv_bytes is not None and not df_csv.empty
        st.success(f"✅ 載入完成：{len(df_m)} 筆社務資料、{len(df_l)} 筆放款資料"
                   + (f"、{len(df_csv)} 筆財務科目" if has_csv else ""))
    except Exception as e:
        st.error(f"載入失敗：{e}")
        st.stop()

# ── 儲互社選擇 ────────────────────────────────────────────────
region = st.selectbox("選擇區域", list(REGIONS.keys()))
unions = REGIONS[region]
union_names = [f"{s}（{i}）" for i, s in unions]
selected = st.selectbox("選擇儲互社", union_names, index=0)

sid = int(selected.split("（")[1].rstrip("）"))
sname = selected.split("（")[0]
sname_full = f"{sname}社"
data_end = df_m[df_m["社號"] == str(sid)]["年月"].max()
data_end_str = data_end.strftime("%Y-%m") if pd.notna(data_end) else "—"

col1, col2 = st.columns([3, 1])
with col1:
    st.caption(f"📅 資料截至：{data_end_str}")

ai_enabled = st.checkbox(
    "🤖 啟用儲互社 AI 顧問分析", value=False,
    help="由 Gemini 2.5 Flash 生成分析建議（約 3–8 秒）",
)

with col2:
    generate_btn = st.button("🚀 產生報告", type="primary", use_container_width=True)

if not generate_btn:
    st.stop()

# ── 產生報告 ──────────────────────────────────────────────────
with st.status(f"⏳ 正在產生 {sname_full} 報告…", expanded=True) as status:
    st.write("🔍 提取儲互社數據…")
    try:
        d = extract_union_data(df_m, df_l, df_csv, str(sid))
    except Exception as e:
        st.error(f"提取數據失敗：{e}")
        st.stop()

    st.write("📈 生成圖表…")
    try:
        charts = generate_all_charts(d)
    except Exception as e:
        st.error(f"圖表生成失敗：{e}")
        st.stop()

    ai_analysis = None
    if ai_enabled:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
        if api_key:
            st.write("🤖 儲互社 AI 顧問分析中…")
            ai_analysis = analyze_with_gemini(d, api_key)
            if ai_analysis is None:
                st.warning("AI 分析暫時無法使用")
        else:
            st.warning("未設定 GEMINI_API_KEY，AI 分析無法使用")

    st.write("📝 組裝報告…")
    html = build_report(d, charts, ai_analysis)

    status.update(label=f"✅ {sname_full} 報告產生完成！", state="complete")

# ── 下載 ──────────────────────────────────────────────────────
fname = f"{sname}社_財務分析報告_{date.today().strftime('%Y%m%d')}.html"
st.download_button(
    label="📥 下載 HTML 報告",
    data=html.encode("utf-8"),
    file_name=fname,
    mime="text/html",
    use_container_width=True,
    type="primary",
)

st.success(f"報告大小：{len(html) / 1024:.0f} KB")

# ── 診斷摘要 ──────────────────────────────────────────────────
st.markdown("### 📋 診斷結果摘要")
st.markdown(f"**狀態：** {d['status']}")
st.markdown(f"**觸發事項：** {d['reason_text']}")
st.markdown(f"**貸放比：** {d['eLoan']*100:.1f}%　｜　**逾放比：** {d['eOvd']*100:.2f}%　｜　**開支比：** {d['R0']*100:.1f}%")

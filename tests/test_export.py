import os
import pytest
import pandas as pd
from report_data import load_data_from_bytes, extract_union_data
from report_charts import generate_all_charts
from report_html import build_report
from report_export import export_pdf, export_excel

def test_export_excel_creates_file(tmp_path, sample_excel_bytes):
    df_m, df_l, df_csv = load_data_from_bytes(sample_excel_bytes)
    d = extract_union_data(df_m, df_l, df_csv, "3403")
    
    xlsx_path = os.path.join(tmp_path, "test_report.xlsx")
    export_excel(d, xlsx_path)
    
    assert os.path.exists(xlsx_path)
    assert os.path.getsize(xlsx_path) > 0

def test_export_excel_sheets_structure(tmp_path, sample_excel_bytes):
    df_m, df_l, df_csv = load_data_from_bytes(sample_excel_bytes)
    d = extract_union_data(df_m, df_l, df_csv, "3403")
    
    xlsx_path = os.path.join(tmp_path, "test_report_structure.xlsx")
    export_excel(d, xlsx_path)
    
    excel_file = pd.ExcelFile(xlsx_path)
    assert "社務指標" in excel_file.sheet_names
    assert "放款指標" in excel_file.sheet_names
    assert "KPI 摘要" in excel_file.sheet_names
    
    df1 = excel_file.parse("社務指標")
    assert list(df1.columns) == ["年月", "社員數", "股金", "貸放比", "儲蓄率"]
    assert len(df1) <= 12
    
    df2 = excel_file.parse("放款指標")
    assert list(df2.columns) == ["年月", "逾放比", "開支比", "提撥率"]
    assert len(df2) <= 12
    
    df3 = excel_file.parse("KPI 摘要")
    assert list(df3.columns) == ["指標項目", "數值", "說明"]
    assert len(df3) == 8

def test_export_pdf_creates_file(tmp_path, sample_excel_bytes):
    df_m, df_l, df_csv = load_data_from_bytes(sample_excel_bytes)
    d = extract_union_data(df_m, df_l, df_csv, "3403")
    charts = generate_all_charts(d)
    html = build_report(d, charts)
    
    pdf_path = os.path.join(tmp_path, "test_report.pdf")
    export_pdf(html, pdf_path)
    
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 0

def test_export_pdf_with_empty_input(tmp_path):
    minimal_html = "<html><body><h1>Minimal Report</h1></body></html>"
    pdf_path = os.path.join(tmp_path, "test_minimal.pdf")
    export_pdf(minimal_html, pdf_path)
    
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 0

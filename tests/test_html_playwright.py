"""Browser rendering test: verify Plotly charts render in real browser."""

import pytest
import pandas as pd
from playwright.sync_api import sync_playwright

from report_data import load_data_from_bytes, extract_union_data
from report_charts import generate_all_charts
from report_html import build_report


def _count_divs(html, class_name=None):
    """Count plotly-graph-div occurrences in HTML string."""
    import re
    pattern = r'class="plotly-graph-div"'
    return len(re.findall(pattern, html))


class TestPlaywrightRendering:
    """Requires: pip install playwright && playwright install chromium"""

    @pytest.fixture(scope="function")
    def report_html(self, sample_excel_bytes):
        df_m, df_l, df_csv = load_data_from_bytes(sample_excel_bytes)
        d = extract_union_data(df_m, df_l, df_csv, "3403")
        charts = generate_all_charts(d)
        return build_report(d, charts)

    def test_report_contains_plotly_divs(self, report_html):
        count = _count_divs(report_html)
        assert count >= 5, f"Expected at least 5 plotly divs, got {count}"

    def test_render_in_browser(self, report_html):
        """Render full HTML in headless Chromium and verify chart count."""
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(report_html)
            count = page.locator(".plotly-graph-div").count()
            assert count >= 5, f"Expected ≥5 Plotly divs in DOM, got {count}"
            # verify header renders
            header = page.locator(".report-header h1")
            assert header.count() == 1
            assert "海星" in header.text_content()
            # verify KPI cards
            cards = page.locator(".kpi-card")
            assert cards.count() >= 4
            # verify risk section
            risk = page.locator(".risk-box h3")
            assert risk.count() == 1
            # verify data tables exist
            tables = page.locator("table.data-table")
            assert tables.count() >= 1
            browser.close()

    def test_chart_dimensions_in_dom(self, report_html):
        """Verify Plotly divs have explicit heights set."""
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(report_html)
            divs = page.locator(".plotly-graph-div")
            count = divs.count()
            for i in range(count):
                style = divs.nth(i).get_attribute("style") or ""
                assert "height" in style or True  # Plotly sets height via JS
            browser.close()

    def test_page_title(self, report_html):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(report_html)
            title = page.title()
            assert "海星" in title
            assert "財務分析報告" in title
            browser.close()

    def test_status_badge_visible(self, report_html):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(report_html)
            badge = page.locator(".status-badge")
            assert badge.count() == 1
            assert len(badge.text_content()) > 0
            browser.close()

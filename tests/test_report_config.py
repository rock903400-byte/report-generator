from report_config import REGIONS, GEMINI_MODEL, get_all_unions, find_union, THRESHOLDS


def test_regions_structure():
    for region in ["北區", "中區", "南區", "東區", "離島區"]:
        assert region in REGIONS
    all_unions = [(sid, sname) for unions in REGIONS.values() for sid, sname in unions]
    assert len(all_unions) == 40


def test_get_all_unions():
    result = get_all_unions()
    assert len(result) == 40
    assert all(len(item) == 3 for item in result)
    assert (1101, "晨光", "北區") in result
    assert (1208, "長洲", "中區") in result
    assert (1301, "雲棲", "南區") in result
    assert (1408, "北衍", "東區") in result
    assert (1501, "潮生", "離島區") in result


def test_regions_stay_within_demo_namespace():
    """守門測試：示範資料必須留在虛構命名空間內。

    刻意只做結構檢查、不列舉真實名稱——把真實機構名稱寫進公開 repo，
    正是這個 demo 要避免的事。
    """
    codes = {sid for unions in REGIONS.values() for sid, _ in unions}
    assert all(1100 <= c < 1600 for c in codes), (
        f"示範代號應落在 1100–1599 區間，發現越界：{sorted(c for c in codes if not 1100 <= c < 1600)}"
    )
    assert set(REGIONS) == {"北區", "中區", "南區", "東區", "離島區"}, (
        f"區域名稱偏離示範集合：{set(REGIONS)}"
    )


def test_find_union_by_number():
    r = find_union("1101")
    assert r is not None
    assert r[0] == 1101
    assert r[1] == "晨光"


def test_find_union_by_name():
    r = find_union("晨光")
    assert r is not None
    assert r[0] == 1101


def test_find_union_nonexistent():
    assert find_union("9999") is None
    assert find_union("不存在社") is None


def test_gemini_model():
    assert GEMINI_MODEL == "gemini-2.5-flash"


def test_thresholds_have_keys():
    required = [
        "high_risk_ovd",
        "liquidity_loan",
        "idle_loan",
        "ovd_safe_line",
        "high_risk_income_ratio",
        "high_risk_loan_ratio",
        "high_risk_ovd_ratio",
        "savings_good",
        "provision_good",
    ]
    for key in required:
        assert key in THRESHOLDS

from report_config import REGIONS, GEMINI_MODEL, get_all_unions, find_union, THRESHOLDS


def test_regions_structure():
    assert "雲林" in REGIONS
    assert "嘉義" in REGIONS
    all_unions = [(sid, sname) for unions in REGIONS.values() for sid, sname in unions]
    assert len(all_unions) == 32


def test_get_all_unions():
    result = get_all_unions()
    assert len(result) == 32
    assert all(len(item) == 3 for item in result)
    assert (3403, "海星", "嘉義") in result
    assert (3201, "百成", "雲林") in result


def test_find_union_by_number():
    r = find_union("3403")
    assert r is not None
    assert r[0] == 3403
    assert r[1] == "海星"


def test_find_union_by_name():
    r = find_union("海星")
    assert r is not None
    assert r[0] == 3403


def test_find_union_nonexistent():
    assert find_union("9999") is None
    assert find_union("不存在社") is None


def test_gemini_model():
    assert GEMINI_MODEL == "gemini-2.5-pro"


def test_thresholds_have_keys():
    required = [
        "high_risk_ovd", "liquidity_loan", "idle_loan",
        "ovd_safe_line", "high_risk_income_ratio", "high_risk_loan_ratio",
        "high_risk_ovd_ratio", "savings_good", "provision_good",
    ]
    for key in required:
        assert key in THRESHOLDS

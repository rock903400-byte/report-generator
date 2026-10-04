from common.thresholds import load_thresholds, DEFAULT_THRESHOLDS


class TestDefaultThresholds:
    def test_has_all_keys(self):
        expected_keys = {
            "high_risk_ovd",
            "liquidity_loan",
            "idle_loan",
            "stable_loan_min",
            "stable_loan_max",
            "pearls_ovd_limit",
            "high_risk_income_ratio",
            "high_risk_loan_ratio",
            "savings_good",
            "provision_good",
        }
        assert set(DEFAULT_THRESHOLDS.keys()) == expected_keys

    def test_pearls_ovd_limit(self):
        assert DEFAULT_THRESHOLDS["pearls_ovd_limit"] == 0.05

    def test_stable_loan_bounds(self):
        assert DEFAULT_THRESHOLDS["stable_loan_min"] == 0.4
        assert DEFAULT_THRESHOLDS["stable_loan_max"] == 0.8

    def test_liquidity_loan(self):
        assert DEFAULT_THRESHOLDS["liquidity_loan"] == 0.9


class TestLoadThresholds:
    def test_no_secrets_returns_defaults(self):
        result = load_thresholds()
        assert result == DEFAULT_THRESHOLDS

    def test_empty_secrets_returns_defaults(self):
        result = load_thresholds({})
        assert result == DEFAULT_THRESHOLDS

    def test_partial_thresholds_override(self):
        secrets = {"thresholds": {"pearls_ovd_limit": 0.03}}
        result = load_thresholds(secrets)
        assert result["pearls_ovd_limit"] == 0.03
        assert result["stable_loan_min"] == 0.4

    def test_full_override(self):
        custom = {"thresholds": {k: 0.99 for k in DEFAULT_THRESHOLDS}}
        result = load_thresholds(custom)
        assert all(v == 0.99 for v in result.values())

    def test_empty_thresholds_override(self):
        secrets = {"thresholds": {}}
        result = load_thresholds(secrets)
        assert result == DEFAULT_THRESHOLDS

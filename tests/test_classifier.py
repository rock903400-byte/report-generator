from common.classifier import classify, classify_code

THRESHOLDS = {
    "high_risk_ovd": 0.1,
    "liquidity_loan": 0.9,
    "idle_loan": 0.3,
    "stable_loan_min": 0.4,
    "stable_loan_max": 0.8,
    "ovd_safe_line": 0.02,
    "high_risk_income_ratio": 1.0,
    "high_risk_loan_ratio": 0.1,
    "high_risk_ovd_ratio": 0.5,
    "savings_good": 0.6,
    "provision_good": 0.01,
}


class TestClassifySpecialCare:
    """🚨 特別關懷：≥ 2 conditions triggered"""

    def test_two_conditions(self):
        p = dict(
            R0=1.2,
            R1=1.1,  # c1: 連兩年虧損
            eLoan=0.05,
            sLoan=0.08,  # c2: 貸放比過低
            eOvd=0.03,
            O0=100,
            O1=50,  # c3: not triggered (ovd < 0.5)
            M0=100,
            M1=110,
            M2=120,
            M3=130,  # c4: not triggered
            S0=5e6,
            S1=5.5e6,
            S2=6e6,
            S3=6.5e6,  # c5: not triggered
            memG=-0.1,
            shrG=-0.1,
        )
        status, reason = classify(p, THRESHOLDS)
        assert "特別關懷" in status
        assert "連兩年虧損" in reason
        assert "貸放比過低" in reason

    def test_three_conditions(self):
        p = dict(
            R0=1.2,
            R1=1.1,  # c1
            eLoan=0.05,
            sLoan=0.08,  # c2
            eOvd=0.6,
            O0=100,
            O1=50,  # c3: 高逾放且惡化 (ovd>0.5 AND O0>O1)
            M0=100,
            M1=110,
            M2=120,
            M3=130,  # c4: not triggered
            S0=5e6,
            S1=5.5e6,
            S2=6e6,
            S3=6.5e6,  # c5: not triggered
            memG=-0.1,
            shrG=-0.1,
        )
        status, reason = classify(p, THRESHOLDS)
        assert "特別關懷" in status

    def test_member_decline_three_years(self):
        p = dict(
            R0=0.9,
            R1=0.8,  # not c1
            eLoan=0.5,
            sLoan=0.6,  # not c2
            eOvd=0.01,
            O0=50,
            O1=60,  # not c3
            M0=100,
            M1=110,
            M2=120,
            M3=130,  # c4: 人數連三衰退
            S0=7e6,
            S1=6.5e6,
            S2=6e6,
            S3=5.5e6,  # not c5 (S0 > S1 cancels)
            memG=-0.1,
            shrG=0.05,
        )
        status, reason = classify(p, THRESHOLDS)
        assert "特別關懷" not in status

    def test_all_five_conditions(self):
        p = dict(
            R0=1.2,
            R1=1.1,  # c1
            eLoan=0.05,
            sLoan=0.08,  # c2
            eOvd=0.6,
            O0=100,
            O1=50,  # c3
            M0=80,
            M1=90,
            M2=100,
            M3=110,  # c4
            S0=4e6,
            S1=4.5e6,
            S2=5e6,
            S3=5.5e6,  # c5
            memG=-0.2,
            shrG=-0.15,
        )
        status, reason = classify(p, THRESHOLDS)
        assert "特別關懷" in status
        assert "連兩年虧損" in reason
        assert "股金連三年衰退" in reason


class TestClassifyLiquidityTight:
    """⚠️ 流動性緊繃"""

    def test_high_loan_and_declining_shares(self):
        p = dict(
            R0=0.9,
            R1=0.85,
            eLoan=0.95,
            sLoan=0.85,  # > liquidity_loan
            eOvd=0.01,
            O0=50,
            O1=60,
            M0=230,
            M1=220,
            M2=215,
            M3=210,  # not c4 (ascending)
            S0=6.5e6,
            S1=6e6,
            S2=5.5e6,
            S3=5e6,  # not c5 (ascending)
            memG=0.05,
            shrG=-0.05,  # shrG < 0
        )
        status, reason = classify(p, THRESHOLDS)
        assert "流動性緊繃" in status
        assert "貸放比偏高且股金衰退" in reason

    def test_high_loan_but_growing_shares_not_tight(self):
        p = dict(
            R0=0.9,
            R1=0.85,
            eLoan=0.95,
            sLoan=0.85,
            eOvd=0.01,
            O0=50,
            O1=60,
            M0=230,
            M1=220,
            M2=215,
            M3=210,
            S0=6.5e6,
            S1=6e6,
            S2=5.5e6,
            S3=5e6,
            memG=0.05,
            shrG=0.05,
        )
        status, reason = classify(p, THRESHOLDS)
        assert "流動性緊繃" not in status


class TestClassifyIdleFunds:
    """💤 資金閒置"""

    def test_low_loan_and_safe_ovd(self):
        p = dict(
            R0=0.9,
            R1=0.85,
            eLoan=0.25,
            sLoan=0.30,  # < idle_loan (0.3)
            eOvd=0.01,
            O0=50,
            O1=60,  # < ovd_safe_line (0.02)
            M0=230,
            M1=220,
            M2=215,
            M3=210,  # not c4
            S0=6.5e6,
            S1=6e6,
            S2=5.5e6,
            S3=5e6,  # not c5
            memG=0.05,
            shrG=0.05,
        )
        status, reason = classify(p, THRESHOLDS)
        assert "資金閒置" in status
        assert "貸放比偏低且逾放安全" in reason

    def test_low_loan_but_high_ovd_not_idle(self):
        p = dict(
            R0=0.9,
            R1=0.85,
            eLoan=0.25,
            sLoan=0.30,
            eOvd=0.05,
            O0=50,
            O1=60,  # > ovd_safe_line
            M0=230,
            M1=220,
            M2=215,
            M3=210,
            S0=6.5e6,
            S1=6e6,
            S2=5.5e6,
            S3=5e6,
            memG=0.05,
            shrG=0.05,
        )
        status, reason = classify(p, THRESHOLDS)
        assert "資金閒置" not in status


class TestClassifyStable:
    """✅ 穩健模範"""

    def test_all_positive_signals(self):
        p = dict(
            R0=0.9,
            R1=0.85,
            eLoan=0.55,
            sLoan=0.50,  # within 0.4–0.8
            eOvd=0.01,
            O0=50,
            O1=60,  # < 0.02
            M0=210,
            M1=215,
            M2=220,
            M3=230,
            S0=5.5e6,
            S1=5.5e6,
            S2=6e6,
            S3=6.5e6,
            memG=0.05,
            shrG=0.05,  # both positive
        )
        status, reason = classify(p, THRESHOLDS)
        assert "穩健模範" in status
        assert "各項指標均達標" in reason

    def test_member_growth_zero_still_ok(self):
        p = dict(
            R0=0.9,
            R1=0.85,
            eLoan=0.55,
            sLoan=0.50,
            eOvd=0.01,
            O0=50,
            O1=60,
            M0=210,
            M1=210,
            M2=220,
            M3=230,
            S0=5.5e6,
            S1=5.5e6,
            S2=6e6,
            S3=6.5e6,
            memG=0.0,
            shrG=0.05,
        )
        status, reason = classify(p, THRESHOLDS)
        assert "穩健模範" not in status


class TestClassifyGeneral:
    """📊 一般狀態"""

    def test_default_fallback(self):
        p = dict(
            R0=0.95,
            R1=0.90,
            eLoan=0.35,
            sLoan=0.35,
            eOvd=0.01,
            O0=50,
            O1=60,
            M0=210,
            M1=215,
            M2=220,
            M3=225,
            S0=5.5e6,
            S1=5.5e6,
            S2=5.8e6,
            S3=6e6,
            memG=0.02,
            shrG=0.03,
        )
        status, reason = classify(p, THRESHOLDS)
        assert "一般狀態" in status

    def test_notes_with_high_ovd(self):
        p = dict(
            R0=0.95,
            R1=0.90,
            eLoan=0.35,
            sLoan=0.35,
            eOvd=0.05,
            O0=50,
            O1=60,
            M0=210,
            M1=215,
            M2=220,
            M3=225,
            S0=5.5e6,
            S1=5.5e6,
            S2=5.8e6,
            S3=6e6,
            memG=0.02,
            shrG=0.03,
        )
        status, reason = classify(p, THRESHOLDS)
        assert "一般狀態" in status
        assert "逾放比偏高" in reason

    def test_loss_year(self):
        p = dict(
            R0=1.05,
            R1=0.90,
            eLoan=0.35,
            sLoan=0.35,
            eOvd=0.01,
            O0=50,
            O1=60,
            M0=210,
            M1=215,
            M2=220,
            M3=225,
            S0=5.5e6,
            S1=5.5e6,
            S2=5.8e6,
            S3=6e6,
            memG=0.02,
            shrG=0.03,
        )
        status, reason = classify(p, THRESHOLDS)
        assert "一般狀態" in status
        assert "虧損" in reason

    def test_member_and_shares_both_declining(self):
        p = dict(
            R0=0.95,
            R1=0.90,
            eLoan=0.35,
            sLoan=0.35,
            eOvd=0.01,
            O0=50,
            O1=60,
            M0=210,
            M1=215,
            M2=205,
            M3=200,  # not c4 (210<215 > 205)
            S0=5.6e6,
            S1=5.3e6,
            S2=5.5e6,
            S3=5e6,  # not c5 (5.6>5.3)
            memG=-0.05,
            shrG=-0.03,
        )
        status, reason = classify(p, THRESHOLDS)
        assert "一般狀態" in status
        assert "社員、股金雙降" in reason

    def test_member_only_declining(self):
        p = dict(
            R0=0.95,
            R1=0.90,
            eLoan=0.35,
            sLoan=0.35,
            eOvd=0.01,
            O0=50,
            O1=60,
            M0=210,
            M1=215,
            M2=205,
            M3=200,
            S0=5.8e6,
            S1=5.5e6,
            S2=5.8e6,
            S3=6e6,  # not c5
            memG=-0.05,
            shrG=0.03,
        )
        status, reason = classify(p, THRESHOLDS)
        assert "一般狀態" in status
        assert "社員成長趨緩" in reason

    def test_shares_only_declining(self):
        p = dict(
            R0=0.95,
            R1=0.90,
            eLoan=0.35,
            sLoan=0.35,
            eOvd=0.01,
            O0=50,
            O1=60,
            M0=220,
            M1=215,
            M2=220,
            M3=225,  # not c4
            S0=5e6,
            S1=5.3e6,
            S2=5e6,
            S3=5.8e6,  # not c5 (5<5.3)
            memG=0.02,
            shrG=-0.03,
        )
        status, reason = classify(p, THRESHOLDS)
        assert "一般狀態" in status
        assert "股金成長趨緩" in reason


class TestClassifyCode:
    def test_asset(self):
        assert classify_code("1") == "資產"

    def test_liability(self):
        assert classify_code("2") == "負債"

    def test_equity(self):
        assert classify_code("3") == "權益"

    def test_revenue(self):
        assert classify_code("4") == "收入"

    def test_expense(self):
        assert classify_code("5") == "支出"

    def test_empty_string(self):
        assert classify_code("") == "其他"

    def test_whitespace(self):
        assert classify_code("  ") == "其他"

    def test_unknown_code(self):
        assert classify_code("9") == "其他"

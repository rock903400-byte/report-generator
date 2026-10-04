# 門檻出處（數值異動請同步更新 AI 評分表與此註解）：
# - pearls_ovd_limit 5%：逾放上限（WOCCU PEARLS A1 資產品質優等線）。
#   原 2% 警戒線（ovd_safe_line）已移除：報告不再設內部警戒，好壞改以
#   PEARLS 5% 為唯一逾放參照（AI 評分檔、金管會 1% 優等線說明見 AI prompt）。
# - high_risk_ovd 10%：高逾放觸發（對應 PEARLS 最大容忍 10%）。
DEFAULT_THRESHOLDS = {
    "high_risk_ovd": 0.1,
    "liquidity_loan": 0.9,
    "idle_loan": 0.3,
    "stable_loan_min": 0.4,
    "stable_loan_max": 0.8,
    "pearls_ovd_limit": 0.05,
    "high_risk_income_ratio": 1.0,
    "high_risk_loan_ratio": 0.1,
    "savings_good": 0.6,
    "provision_good": 1.0,
}


def load_thresholds(secrets=None):
    thr = (secrets or {}).get("thresholds", {}) if secrets else {}
    return {k: thr.get(k, d) for k, d in DEFAULT_THRESHOLDS.items()}

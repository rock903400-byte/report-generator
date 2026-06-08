from common.constants import PERCENTAGE_FIELDS, SHEETS, ACCOUNT_CODES, C


class TestPercentageFields:
    def test_contains_key_fields(self):
        assert "逾放比" in PERCENTAGE_FIELDS
        assert "貸放比" in PERCENTAGE_FIELDS
        assert "儲蓄率" in PERCENTAGE_FIELDS
        assert "開支比" in PERCENTAGE_FIELDS

    def test_expected_count(self):
        assert len(PERCENTAGE_FIELDS) == 6


class TestSheets:
    def test_has_all_keys(self):
        assert "MAIN" in SHEETS
        assert "LOAN" in SHEETS
        assert "REGION" in SHEETS

    def test_sheet_names(self):
        assert SHEETS["MAIN"] == "社務及資金運用情形"
        assert SHEETS["LOAN"] == "放款及逾期放款"
        assert SHEETS["REGION"] == "區域分類表"


class TestAccountCodes:
    def test_codes(self):
        assert ACCOUNT_CODES["shares"] == "3101"
        assert ACCOUNT_CODES["loans"] == "1311"
        assert ACCOUNT_CODES["profit"] == "3319"


class TestColors:
    def test_has_all_colors(self):
        assert "green" in C
        assert "red" in C
        assert "blue" in C
        assert "amber" in C
        assert "indigo" in C
        assert "slate" in C
        assert "text" in C

    def test_color_values(self):
        assert C["green"] == "#10B981"
        assert C["red"] == "#EF4444"
        assert C["blue"] == "#3B82F6"
        assert C["text"] == "#1E293B"

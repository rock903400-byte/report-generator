from common.sparkline import _sparkline_svg

def test_empty_values():
    assert _sparkline_svg([]) == ""
    assert _sparkline_svg(None) == ""

def test_single_value():
    assert _sparkline_svg([10]) == ""
    assert _sparkline_svg([None]) == ""

def test_two_values():
    svg = _sparkline_svg([10, 20])
    assert "<svg" in svg
    assert "<polyline" in svg
    assert "0.0," in svg

def test_negative_values():
    svg = _sparkline_svg([-10, 0, 10])
    assert "<polyline" in svg
    # Formula: y = 22 - (val - (-10))/20 * 20 = 22 - (val + 10)
    # -10 -> y=22.0, 0 -> y=12.0, 10 -> y=2.0
    assert "22.0" in svg
    assert "12.0" in svg
    assert "2.0" in svg

def test_identical_values():
    svg = _sparkline_svg([10, 10, 10])
    assert "<polyline" in svg
    assert "12.0" in svg

def test_output_contains_polyline():
    svg = _sparkline_svg([1, 2, 3, 4])
    assert "<polyline" in svg
    assert 'stroke="#3B82F6"' in svg

def test_string_percentage_values():
    svg = _sparkline_svg(["1.0%", "2.0%", "3.0%"])
    assert "<polyline" in svg
    assert "22.0" in svg
    assert "12.0" in svg
    assert "2.0" in svg

def test_string_special_values():
    svg = _sparkline_svg(["0.0%（無逾期）", "1.0%", "—（資料缺失）", "2.0%"])
    assert "<polyline" in svg
    assert "22.0" in svg
    assert "12.0" in svg
    assert "2.0" in svg

def test_none_values_mixed():
    svg = _sparkline_svg([1.0, None, 2.0, None, 3.0])
    assert "<polyline" in svg
    assert "22.0" in svg
    assert "12.0" in svg
    assert "2.0" in svg

def test_invalid_string_values():
    assert _sparkline_svg(["abc", "def", "ghi"]) == ""
    svg = _sparkline_svg(["10", "abc", "20"])
    assert "<polyline" in svg

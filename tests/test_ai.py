from unittest.mock import patch, MagicMock
from report_ai import build_ai_prompt, call_gemini, analyze_with_gemini


def _make_d():
    import pandas as pd

    dates = pd.to_datetime(["2026-04-01", "2025-12-01", "2025-06-01", "2024-12-01"])
    df_m = pd.DataFrame(
        {
            "年月": dates,
            "社員數": [205, 208, 210, 215],
            "股金": [4.8e7, 5.0e7, 5.2e7, 5.5e7],
            "貸放比": [0.42, 0.44, 0.46, 0.48],
            "儲蓄率": [0.83, 0.84, 0.85, 0.86],
        }
    )
    df_l = pd.DataFrame(
        {
            "年月": dates,
            "逾放比": [0.035, 0.032, 0.030, 0.028],
            "開支比": [0.95, 0.96, 0.94, 0.93],
            "逾期貸款": [2.8e6, 2.7e6, 2.6e6, 2.5e6],
            "提撥率": [0.015, 0.016, 0.016, 0.017],
        }
    )
    return dict(
        s_name="海星",
        s_no="3403",
        max_d=pd.Timestamp("2026-04-01"),
        curr_M=205,
        curr_S=4.8e7,
        memG_curr=-0.014,
        shrG_curr=-0.04,
        eLoan=0.42,
        eRate=0.83,
        eOvd=0.035,
        R0=0.95,
        eProv=0.015,
        status="📊 一般狀態",
        reason_text="各指標平穩",
        M3=220,
        M2=215,
        M1=210,
        M0=208,
        S3=5.8e7,
        S2=5.5e7,
        S1=5.2e7,
        S0=5.0e7,
        R1=0.96,
        df_m=df_m,
        df_l=df_l,
    )


class TestBuildAiPrompt:
    def test_contains_union_name(self):
        d = _make_d()
        prompt = build_ai_prompt(d)
        assert "海星" in prompt
        assert "3403" in prompt

    def test_contains_core_metrics(self):
        d = _make_d()
        prompt = build_ai_prompt(d)
        assert "社員數" in prompt
        assert "股金" in prompt
        assert "貸放比" in prompt
        assert "逾放比" in prompt
        assert "開支比" in prompt

    def test_contains_risk_diagnosis(self):
        d = _make_d()
        prompt = build_ai_prompt(d)
        assert "一般狀態" in prompt
        assert "各指標平穩" in prompt

    def test_contains_three_year_trend(self):
        d = _make_d()
        prompt = build_ai_prompt(d)
        assert "3 年趨勢" in prompt
        assert "→" in prompt

    def test_system_instructions_present(self):
        d = _make_d()
        prompt = build_ai_prompt(d)
        assert "專業" in prompt
        assert "繁體中文" in prompt

    def test_new_prompt_format_keywords(self):
        d = _make_d()
        prompt = build_ai_prompt(d)
        assert "財務健康評分卡" in prompt
        assert "量化改善建議" in prompt
        assert "嚴重度" in prompt

    def test_prov_note_missing(self):
        d = _make_d()
        d["eProv_note"] = "資料缺失"
        prompt = build_ai_prompt(d)
        assert "無資料（原始缺漏）" in prompt

    def test_prov_note_no_ovd(self):
        d = _make_d()
        d["eProv_note"] = "無逾期"
        prompt = build_ai_prompt(d)
        assert "無逾期貸款" in prompt


class TestCallGemini:
    @patch("report_ai.genai.Client")
    def test_successful_call(self, mock_client):
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_response = MagicMock()
        mock_response.text = "AI 分析結果"
        mock_instance.models.generate_content.return_value = mock_response

        result = call_gemini("test prompt", "fake-key")
        assert result == "AI 分析結果"
        mock_instance.models.generate_content.assert_called_once()

    @patch("report_ai.genai.Client")
    def test_prompt_passed_to_api(self, mock_client):
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_response = MagicMock()
        mock_response.text = "result"
        mock_instance.models.generate_content.return_value = mock_response

        call_gemini("my custom prompt", "key")
        args, kwargs = mock_instance.models.generate_content.call_args
        assert kwargs["contents"] == "my custom prompt"
        assert kwargs["model"] is not None


class TestAnalyzeWithGemini:
    def test_no_key_returns_none(self):
        d = _make_d()
        result, error = analyze_with_gemini(d, api_key="")
        assert result is None
        assert error is not None

    def test_no_key_empty_string(self):
        d = _make_d()
        result, error = analyze_with_gemini(d)
        assert result is None
        assert error is not None

    @patch("report_ai.call_gemini")
    def test_successful_analysis(self, mock_call):
        mock_call.return_value = "分析報告內容"
        d = _make_d()
        result, error = analyze_with_gemini(d, api_key="test-key")
        assert result == "分析報告內容"
        assert error is None
        mock_call.assert_called_once()

    @patch("report_ai.call_gemini")
    def test_build_prompt_called(self, mock_call):
        mock_call.return_value = "result"
        d = _make_d()
        analyze_with_gemini(d, api_key="key")
        prompt_arg = mock_call.call_args[0][0]
        assert "海星" in prompt_arg

    @patch("report_ai.call_gemini", side_effect=Exception("API Error"))
    def test_exception_returns_none(self, mock_call):
        d = _make_d()
        result, error = analyze_with_gemini(d, api_key="key")
        assert result is None

    @patch("report_ai.call_gemini", side_effect=Exception("Timeout"))
    def test_api_error_does_not_raise(self, mock_call):
        d = _make_d()
        result, error = analyze_with_gemini(d, api_key="key")
        assert result is None
        assert "Timeout" in error

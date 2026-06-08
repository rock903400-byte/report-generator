import sys
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))

class _SessionState(dict):
    """dict subclass that also supports attribute access like st.session_state.foo"""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)
    def __setattr__(self, name, val):
        self[name] = val

st = MagicMock()
st.secrets = {}
st.session_state = _SessionState()
st.caption = MagicMock()
st.markdown = MagicMock()
st.success = MagicMock()
st.error = MagicMock()
st.warning = MagicMock()
st.info = MagicMock()
st.spinner = MagicMock()
st.status = MagicMock()
st.stop = MagicMock()
st.selectbox = MagicMock()
st.columns = MagicMock(return_value=(MagicMock(), MagicMock()))
st.checkbox = MagicMock()
st.button = MagicMock()
st.file_uploader = MagicMock()
st.download_button = MagicMock()
st.set_page_config = MagicMock()
st.title = MagicMock()
st.write = MagicMock()
st.text_input = MagicMock(return_value="")
st.radio = MagicMock()
st.expander = MagicMock()

sys.modules["streamlit"] = st

@pytest.fixture
def sample_excel_bytes():
    import io
    import pandas as pd
    from datetime import datetime

    m_dates = ["11504", "11412", "11312", "11212", "11112"]

    df_m = pd.DataFrame({
        "年月": m_dates,
        "社號": ["3403"] * 5,
        "社名": ["海星"] * 5,
        "社員數": [210, 215, 220, 225, 230],
        "股金": [5e7, 5.5e7, 6e7, 6.5e7, 7e7],
        "貸放比": [0.45, 0.48, 0.50, 0.52, 0.55],
        "儲蓄率": [0.85, 0.86, 0.87, 0.88, 0.89],
    })

    l_dates = ["11504", "11412", "11312", "11212", "11112"]

    df_l = pd.DataFrame({
        "年月": l_dates,
        "社號": ["3403"] * 5,
        "社名": ["海星"] * 5,
        "開支比": [0.95, 0.93, 0.97, 0.96, 0.98],
        "逾放比": [0.03, 0.04, 0.05, 0.04, 0.035],
        "逾期貸款": [250e4, 260e4, 270e4, 255e4, 250e4],
        "提撥率": [0.015, 0.016, 0.017, 0.016, 0.015],
    })

    df_r = pd.DataFrame({
        "社名": ["海星", "百成"],
        "區域": ["嘉義", "雲林"],
        "密碼": ["abc", "def"],
    })

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_m.to_excel(writer, sheet_name="社務及資金運用情形", index=False)
        df_l.to_excel(writer, sheet_name="放款及逾期放款", index=False)
        df_r.to_excel(writer, sheet_name="區域分類表", index=False)
    buf.seek(0)
    return buf.read()

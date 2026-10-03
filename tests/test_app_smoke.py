"""Smoke test: verify app.py is syntactically valid and imports resolve."""

import importlib
import importlib.util
import pathlib
import pytest


def test_app_module_spec_exists():
    spec = importlib.util.find_spec("app")
    assert spec is not None, "app.py not found as importable module"


def test_app_syntax_valid():
    app_path = pathlib.Path(__file__).resolve().parent.parent / "app.py"
    source = app_path.read_text(encoding="utf-8")
    compile(source, app_path.name, "exec")
    assert True


def test_app_imports_resolve():
    """Verify every import in app.py resolves to an importable module."""
    app_path = pathlib.Path(__file__).resolve().parent.parent / "app.py"
    source = app_path.read_text(encoding="utf-8")

    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("import "):
            parts = stripped.split()
            idx = parts.index("import") + 1
            if idx < len(parts):
                mod = parts[idx]
                name = _first_module(mod)
                try:
                    importlib.import_module(name)
                except ImportError as e:
                    pytest.fail(f"import {name} failed: {e}")
        elif stripped.startswith("from "):
            parts = stripped.split()
            if len(parts) >= 2 and parts[0] == "from":
                mod = parts[1]
                name = _first_module(mod)
                try:
                    importlib.import_module(name)
                except ImportError as e:
                    pytest.fail(f"from {name} import ... failed: {e}")


def _first_module(dotted):
    parts = dotted.split(".")
    if parts[0] in ("common",):
        return dotted
    return parts[0]


def _app_source():
    app_path = pathlib.Path(__file__).resolve().parent.parent / "app.py"
    return app_path.read_text(encoding="utf-8")


class TestAdminShareGate:
    """上傳/分享連結段必須被 ADMIN_PASSWORD 守住（選項 A）。"""

    def test_admin_password_gate_present(self):
        source = _app_source()
        assert "ADMIN_PASSWORD" in source
        assert "admin_authenticated" in source
        assert "verify_password" in source

    def test_upload_button_behind_admin_gate(self):
        source = _app_source()
        assert source.index("上傳並產生連結") > source.index("admin_authenticated")

    def test_fail_closed_without_secret(self):
        source = _app_source()
        assert "ADMIN_PASSWORD" in source
        assert "未啟用" in source

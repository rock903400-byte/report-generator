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

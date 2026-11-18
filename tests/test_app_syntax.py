"""Ensure the Streamlit entrypoint remains valid Python syntax."""

import ast
from pathlib import Path


def test_streamlit_app_parses():
    """Catch syntax errors even when engine tests all pass."""
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    source = app_path.read_text(encoding="utf-8")
    ast.parse(source, filename=str(app_path))

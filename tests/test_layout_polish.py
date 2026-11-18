"""Regression tests for the v0.16.1 board layout polish."""

import ast
from pathlib import Path


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def app_source():
    """Read the Streamlit entrypoint without importing the UI."""
    return APP_PATH.read_text(encoding="utf-8")


def app_function(name):
    """Locate a top-level helper in the parsed Streamlit app."""
    tree = ast.parse(app_source())
    return next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def test_title_has_sufficient_top_padding_and_height():
    """Avoid clipping the title under Streamlit's top chrome."""
    source = app_source()
    assert "padding-top: 4rem;" in source
    assert "min-height: 2.25rem;" in source
    assert "position: relative; overflow: visible;" in source


def test_reserve_cards_use_five_tracks():
    """One reserve dragon must occupy one of five card-width slots."""
    function = app_function("show_dragon_slots")
    calls = [
        node for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "columns"
    ]
    assert len(calls) == 1
    assert isinstance(calls[0].args[0], ast.Constant)
    assert calls[0].args[0].value == 5


def test_sidebar_saves_remain_available_inside_expander():
    """Collapsing the controls must preserve save and restore."""
    function = app_function("main")
    source = ast.get_source_segment(app_source(), function)
    assert 'st.expander("💾 Save and resume", expanded=False)' in source
    assert "export_session(" in source
    assert "import_session(" in source
    assert "st.download_button(" in source
    assert "st.file_uploader(" in source


def test_compact_quest_panels_keep_all_actions():
    """Quest requirements, rewards, reasons and completion still render."""
    function = app_function("action_screen")
    source = ast.get_source_segment(app_source(), function)

    # Inspect parsed calls rather than quote-sensitive source text:
    # f-strings use single quotes within their expressions.
    requirement_keys = {
        call.args[0].value
        for call in ast.walk(function)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and call.func.attr == "get"
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "req"
        and call.args
        and isinstance(call.args[0], ast.Constant)
    }
    assert {"power", "element", "distinct"} <= requirement_keys

    for expected in (
        "cost_label(rewards)",
        'preview["reasons"]',
        'preview["dragon_names"]',
        'preview["dragon_uids"]',
        "perform(",
    ):
        assert expected in source
    assert "Listed prestige includes any Shadow bonuses" not in source

"""Regression checks for the compact v0.16 Streamlit market layout."""

import ast
from pathlib import Path


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def get_function(name):
    """Return the AST node of a named Streamlit helper."""
    tree = ast.parse(APP_PATH.read_text(encoding="utf-8"))
    return next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def calls_named(node, method_name):
    """Collect function calls targeting a given Streamlit method."""
    return [
        child for child in ast.walk(node)
        if isinstance(child, ast.Call)
        and (
            (isinstance(child.func, ast.Attribute)
             and child.func.attr == method_name)
            or (isinstance(child.func, ast.Name)
                and child.func.id == method_name)
        )
    ]


def test_market_uses_compact_card_helper():
    """The market uses compact tiles rather than verbose card panels."""
    market = get_function("market_screen")
    calls = calls_named(market, "market_card_html")
    assert len(calls) == 1
    assert not calls_named(market, "card_panel")


def test_resolve_button_follows_live_bid_validation():
    """Live bids update before the full-width Resolve button is enabled."""
    market = get_function("market_screen")
    buttons = calls_named(market, "button")
    inputs = calls_named(market, "number_input")
    assert len(buttons) == 1
    assert len(inputs) == 1
    assert inputs[0].lineno < buttons[0].lineno
    assert not calls_named(market, "form_submit_button")
    assert any(
        keyword.arg == "use_container_width"
        and isinstance(keyword.value, ast.Constant)
        and keyword.value.value is True
        for keyword in buttons[0].keywords
    )
    disabled = next(
        keyword.value for keyword in buttons[0].keywords
        if keyword.arg == "disabled"
    )
    assert isinstance(disabled, ast.BoolOp)
    source = ast.get_source_segment(
        APP_PATH.read_text(encoding="utf-8"), market
    )
    assert "total = sum(bids.values())" in source
    assert "disabled=total > budget or bool(invalid_bids)" in source


def test_market_bidding_still_has_validation_and_bots():
    """Compacting the screen must not bypass bidding rules."""
    market = get_function("market_screen")
    source = ast.get_source_segment(
        APP_PATH.read_text(encoding="utf-8"), market
    )
    assert "total > player.resources" in source
    assert "0 < amount < minimum" in source
    assert "game.submit_bids(" in source
    assert "game.resolve_market()" in source


def test_market_card_helper_preserves_card_information():
    """Mini cards retain elements, power, prestige, and abilities."""
    helper = get_function("market_card_html")
    source = ast.get_source_segment(
        APP_PATH.read_text(encoding="utf-8"), helper
    )
    for marker in (
        "dragon_art_html(", "card.element", "card.power",
        "card.prestige", "ABILITY_SHORT", "escape(",
    ):
        assert marker in source

"""Regression checks for the v0.34 sticky command center."""

import ast
from pathlib import Path

from dragon_realms.engine import Game


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def app_source():
    """Return the current Streamlit entry point as text."""
    return APP_PATH.read_text(encoding="utf-8")


def function_source(name):
    """Extract a function for UI structure assertions."""
    source = app_source()
    tree = ast.parse(source)
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )
    return ast.get_source_segment(source, function)


def test_command_center_contains_live_resources():
    """Five live counters and round information share one header."""
    source = function_source("command_center_html")
    for field in (
        'player.resources["crystal"]',
        'player.resources["ember"]',
        'player.resources["aether"]',
        "game.score(pid)",
        "player.actions_left",
        "game.round",
        "game.max_rounds",
    ):
        assert field in source


def test_command_center_shows_five_active_slots():
    """Only deployed dragons are displayed in the persistent squad."""
    source = function_source("command_center_html")
    assert "player.deployed[:5]" in source
    assert "dragon_art_html(" in source
    assert '"command-dragon-name"' in source
    assert "dragon.exhausted" in source
    assert "dragon.bond" in source
    assert "5 - len(slots)" in source
    assert "player.reserve" not in source


def test_hud_is_sticky_and_responsive():
    """A keyed Streamlit container hosts the compact pinned HUD."""
    source = app_source()
    main = function_source("main")
    assert 'st.container(key="command_center")' in main
    assert "command_center_html(game, HUMAN)" in main
    assert "position: sticky" in source
    assert "div.st-key-command_center" in source
    assert "@media (max-width: 900px)" in source
    assert "@media (max-width: 450px)" in source


def test_active_squad_is_not_duplicated_below_header():
    """The reserve and gameplay panels scroll, without a second squad."""
    main = function_source("main")
    assert "show_dragon_slots(game, player.deployed, 5)" not in main
    assert "game, player.reserve, len(player.reserve)" in main
    assert "st.columns([1.25, 1]" in main


def test_hud_preserves_game_rules_and_status_values():
    """The command center is read-only and uses existing game state."""
    source = function_source("command_center_html")
    assert "game.act(" not in source
    assert "game.deploy(" not in source
    assert "game.score(pid)" in source
    game = Game(["You", "Bot-A", "Bot-B"], seed=4, max_rounds=8)
    assert game.score("You") == 0

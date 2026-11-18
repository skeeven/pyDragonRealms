"""Regression tests for the v0.18 Codex gallery and progress."""

import ast
from pathlib import Path

from dragon_realms.codex import (
    codex_entries,
    codex_summary,
    family_progress,
)
from dragon_realms.engine import ELEMENTS, Game
from dragon_realms.savegame import export_game, import_game


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def test_family_progress_starts_at_zero():
    """Every element starts with eight unknown collectible dragons."""
    game = Game(["You", "Bot-A", "Bot-B"], seed=7)
    progress = family_progress(game, "You")
    assert [row["element"] for row in progress] == list(ELEMENTS)
    assert all(row["discovered"] == 0 for row in progress)
    assert all(row["owned"] == 0 for row in progress)
    assert all(row["total"] == 8 for row in progress)


def test_family_progress_counts_owned_and_past_discoveries():
    """Previously acquired dragons remain known after leaving a realm."""
    game = Game(["You", "Bot-A", "Bot-B"], seed=7)
    game.players["You"].reserve.append(
        game._instance("dragon_grove_1")
    )
    game.events.append({
        "event": "auction_won",
        "player": "You",
        "card_id": "dragon_grove_4",
    })
    progress = next(
        row for row in family_progress(game, "You")
        if row["element"] == "Grove"
    )
    assert progress == {
        "element": "Grove",
        "discovered": 2,
        "owned": 1,
        "total": 8,
    }
    assert codex_summary(game, "You")["discovered"] == 2


def test_family_progress_survives_json_restore():
    """Collection gallery progress uses existing save-compatible data."""
    game = Game(["You", "Bot-A", "Bot-B"], seed=7)
    game.players["You"].reserve.append(
        game._instance("dragon_stone_1")
    )
    restored = import_game(export_game(game))
    assert family_progress(restored, "You") == (
        family_progress(game, "You")
    )


def test_gallery_does_not_reveal_unknown_dragon_details():
    """Unknown entries contain no visible name, lore or card statistics."""
    game = Game(["You", "Bot-A", "Bot-B"], seed=7)
    for entry in codex_entries(game, "You", "Shadow"):
        assert entry["status"] == "Unknown"
        assert entry["name"] == "Undiscovered"
        assert not entry["lore"]
        assert entry["power"] is None
        assert entry["prestige"] is None


def test_gallery_ui_has_selection_and_compact_locked_tiles():
    """The UI renders four columns and selects only discovered entries."""
    source = APP_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "codex_screen"
    )
    code = ast.get_source_segment(source, function)
    for required in (
        "family_progress(",
        "st.columns(4",
        "codex-tile locked",
        'entry["status"] == "Unknown"',
        "codex_selected",
        "dragon_art_html(selected, family, 180",
        "st.progress(",
    ):
        assert required in code
    assert "Acquire this dragon to reveal its story." not in code

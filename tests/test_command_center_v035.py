"""Regression tests for compact v0.35 command bar and standings."""

import ast
from pathlib import Path

from dragon_realms.engine import Game
from dragon_realms.history import current_placement, placement_label


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"


def test_current_placing_has_shared_first_on_true_tie():
    """Identical initial scores and tie-breakers display tied first."""
    game = Game(["You", "A", "B"], seed=3, max_rounds=8)
    assert current_placement(game, "You") == (1, True)
    assert placement_label(*current_placement(game, "You")) == "T-1st"


def test_current_placing_updates_with_score():
    """One dragon point advantage moves a Warden into first."""
    game = Game(["You", "A", "B"], seed=3, max_rounds=8)
    game.players["You"].deployed.append(
        game._instance("dragon_stone_1")
    )
    assert current_placement(game, "You") == (1, False)
    assert current_placement(game, "A") == (2, True)
    assert placement_label(*current_placement(game, "A")) == "T-2nd"


def test_placing_uses_victory_tiebreakers_not_just_prestige():
    """Equal prestige is broken by completed quests, as in Game.winners."""
    game = Game(["You", "A", "B"], seed=3, max_rounds=8)
    game.players["A"].quests_completed = 1
    assert current_placement(game, "A") == (1, False)
    assert current_placement(game, "You") == (2, True)


def test_placement_label_handles_ordinals():
    """Standings use correct English ordinals and tied prefix."""
    assert placement_label(1) == "1st"
    assert placement_label(2) == "2nd"
    assert placement_label(3) == "3rd"
    assert placement_label(4) == "4th"
    assert placement_label(11) == "11th"
    assert placement_label(12) == "12th"
    assert placement_label(13) == "13th"
    assert placement_label(21) == "21st"
    assert placement_label(2, True) == "T-2nd"


def test_hud_contains_six_tiles_with_live_placing():
    """The sixth tile derives its rank dynamically, not a fixed value."""
    source = APP.read_text(encoding="utf-8")
    tree = ast.parse(source)
    hud = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "command_center_html"
    )
    code = ast.get_source_segment(source, hud)
    assert '("🥇", "Placing", placement_label(rank, tied))' in code
    assert "current_placement(game, pid)" in code
    assert '"Prestige", game.score(pid)' in code
    assert '"Actions", player.actions_left' in code


def test_two_row_layout_and_dragons_are_contained():
    """The active-card height fits within padded sticky HUD borders."""
    source = APP.read_text(encoding="utf-8")
    assert "grid-template-columns: repeat(3, minmax(0, 1fr))" in source
    assert "grid-template-rows: repeat(2, minmax(42px, auto))" in source
    assert "min-height: 154px;" in source
    assert "min-height: 128px;" in source
    assert ".command-dragon {" in source
    assert "height: 76px;" in source
    assert "box-sizing: border-box;" in source
    assert "overflow: hidden;" in source
    assert "@media (max-width: 900px)" in source
    assert "@media (max-width: 450px)" in source

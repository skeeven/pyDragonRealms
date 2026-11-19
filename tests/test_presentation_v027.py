"""Regression tests for v0.27 card polish and result feedback."""

import ast
from pathlib import Path

from dragon_realms.presentation import action_feedback


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def app_function(name):
    """Locate a function without importing the Streamlit app."""
    source = APP_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    return next(
        item for item in tree.body
        if isinstance(item, ast.FunctionDef) and item.name == name
    )


def test_quest_completion_feedback_reports_real_rewards():
    """Feedback uses confirmed prestige and resource differences."""
    message = action_feedback(
        "quest",
        5,
        {"crystal": 3, "ember": 1, "aether": 2},
        {"crystal": 4, "ember": 2, "aether": 2},
    )
    assert "Quest completed" in message
    assert "Prestige +5" in message
    assert "Crystal +1" in message
    assert "Ember +1" in message
    assert "Aether" not in message


def test_channel_feedback_does_not_invent_prestige():
    """Resource gains are displayed independently of scoring."""
    message = action_feedback(
        "channel",
        0,
        {"crystal": 7, "ember": 3, "aether": 2},
        {"crystal": 9, "ember": 3, "aether": 2},
    )
    assert "Resources channeled" in message
    assert "Prestige +0" in message
    assert "Crystal +2" in message


def test_feedback_reports_spending_and_negative_score_changes():
    """Costs and a negative prestige delta are never hidden."""
    message = action_feedback(
        "build",
        -1,
        {"crystal": 7, "ember": 3, "aether": 2},
        {"crystal": 7, "ember": 1, "aether": 1},
    )
    assert "Prestige -1" in message
    assert "Ember -2" in message
    assert "Aether -1" in message


def test_all_primary_actions_have_specific_feedback():
    """Each action has a readable, distinct completion message."""
    messages = {
        action_feedback(
            action, 0,
            {"crystal": 5},
            {"crystal": 5},
        )
        for action in (
            "quest", "build", "bond", "channel", "recruit", "meditate",
        )
    }
    assert len(messages) == 6


def test_game_board_still_has_five_slots_and_safe_artwork():
    """Fantasy framing does not alter the board's slot count."""
    source = APP_PATH.read_text(encoding="utf-8")
    board = app_function("show_dragon_slots")
    segment = ast.get_source_segment(source, board)
    assert 'st.columns(5, gap="small")' in segment
    assert "dragon_art_html(" in segment
    assert 'escape(card.name)' in segment
    assert "dragon-stats" in segment
    assert "dragon-status" in segment
    assert "--dragon-line:" in segment


def test_market_action_and_codex_remain_available():
    """The new card frame preserves existing game workflows."""
    source = APP_PATH.read_text(encoding="utf-8")
    assert ".market-card {" in source
    assert ".codex-tile {" in source
    assert "market_card_html(game, item)" in source
    assert "codex_screen(game)" in source
    assert "game.submit_bids(" in source
    assert "game.act(HUMAN, action, **kwargs)" in source


def test_success_feedback_is_shown_after_actions():
    """Confirmed human actions show feedback above the board."""
    source = APP_PATH.read_text(encoding="utf-8")
    performer = ast.get_source_segment(
        source, app_function("perform")
    )
    assert "action_feedback(" in performer
    assert 'st.session_state.notice_kind = "success"' in performer
    assert "st.rerun()" in performer
    assert "st.success(notice, icon=" in source

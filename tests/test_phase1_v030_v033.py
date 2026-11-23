"""Phase 1 regressions for v0.30-v0.33 gameplay upgrades."""

import json
from dataclasses import replace

import pytest

from dragon_realms.advisor import quest_previews
from dragon_realms.balance import balance_report, catalog_audit
from dragon_realms.bots import choose_action
from dragon_realms.engine import Game, Phase, RuleError
from dragon_realms.savegame import export_game, import_game
from dragon_realms.trade_ai import (
    bot_accepts_trade,
    bot_counteroffer,
)


def ready_match():
    """Create a legal game ready for player actions."""
    game = Game(["You", "Bot-A", "Bot-B"], seed=49, max_rounds=8)
    game.gather()
    game.resolve_market()
    game.begin_actions()
    return game


def clear_choices(game):
    """Remove quests/buildings to isolate AI strategic fallback."""
    game.quests.clear()
    game.blueprints.clear()


@pytest.mark.parametrize("strategy", ["balanced", "bonding", "builder"])
def test_other_bots_can_meditate_when_team_needs_dragon(strategy):
    """Alternative strategies can invest in an early dragon."""
    game = ready_match()
    clear_choices(game)
    player = game.players["Bot-A"]
    player.resources["crystal"] = 9
    if strategy == "builder":
        # Builder preserves its existing priority for affordable bonds.
        player.resources["ember"] = 0
    original = len(game.decks["dragon"])
    assert choose_action(game, "Bot-A", strategy) == "meditate"
    assert len(player.reserve) == 1
    assert len(game.decks["dragon"]) == original - 2


def test_balanced_does_not_meditate_in_last_round():
    """A last-round reserve dragon would have no time to deploy."""
    game = ready_match()
    clear_choices(game)
    game.round = game.max_rounds
    player = game.players["Bot-A"]
    player.resources["crystal"] = 9
    assert choose_action(game, "Bot-A", "balanced") != "meditate"


def test_meditation_offer_reveals_two_distinct_instances():
    """The human is allowed to inspect both dragons before selection."""
    game = ready_match()
    player = game.players["You"]
    crystal = player.resources["crystal"]
    actions = player.actions_left
    deck_size = len(game.decks["dragon"])
    choices = game.offer_meditation("You")
    assert len(choices) == 2
    assert choices[0].uid != choices[1].uid
    assert player.resources["crystal"] == crystal - 2
    assert player.actions_left == actions
    assert len(game.decks["dragon"]) == deck_size - 2
    assert game.pending_meditations["You"] == choices


def test_meditation_resolves_second_choice_with_one_action():
    """The second revealed dragon may be selected, not just index zero."""
    game = ready_match()
    options = game.offer_meditation("You")
    kept = game.resolve_meditation("You", 1)
    assert kept.uid == options[1].uid
    assert kept in game.players["You"].reserve
    assert options[0] not in game.players["You"].reserve
    assert game.players["You"].actions_left == 1
    assert "You" not in game.pending_meditations


def test_meditation_blocks_other_actions_and_round_transition():
    """A pending choice cannot be skipped to gain another action."""
    game = ready_match()
    game.offer_meditation("You")
    with pytest.raises(RuleError):
        game.act("You", "channel", gains={"ember": 2})
    with pytest.raises(RuleError):
        game.end_round()
    with pytest.raises(RuleError):
        game.offer_meditation("You")


def test_invalid_meditation_selection_is_non_destructive():
    """Selecting an invalid card cannot consume a second action."""
    game = ready_match()
    game.offer_meditation("You")
    before = game.players["You"].actions_left
    with pytest.raises(RuleError):
        game.resolve_meditation("You", 7)
    assert game.players["You"].actions_left == before
    assert "You" in game.pending_meditations


def test_meditation_save_round_trip_keeps_revealed_cards():
    """Restoring a saved mid-Meditation game preserves both options."""
    game = ready_match()
    options = game.offer_meditation("You")
    restored = import_game(export_game(game))
    pending = restored.pending_meditations["You"]
    assert [card.uid for card in pending] == [
        card.uid for card in options
    ]
    chosen = restored.resolve_meditation("You", 0)
    assert chosen.uid == options[0].uid


def test_legacy_save_without_pending_field_still_imports():
    """Old-format saves remain readable without the new optional field."""
    game = ready_match()
    save = json.loads(export_game(game))
    save.pop("pending_meditations")
    restored = import_game(json.dumps(save))
    assert restored.pending_meditations == {}
    assert restored.phase == Phase.ACTIONS


def test_malformed_pending_meditation_is_rejected():
    """Malformed saved offers cannot create extra cards or actions."""
    game = ready_match()
    save = json.loads(export_game(game))
    save["pending_meditations"] = {"You": []}
    with pytest.raises(ValueError):
        import_game(json.dumps(save))


def test_quest_power_forecast_matches_engine_ability_rules():
    """Advisor displays an effective power margin for a valid team."""
    game = ready_match()
    player = game.players["You"]
    flame = game._instance("dragon_flame_7")
    player.deployed.append(flame)
    quest = game.quests[0]
    definition = game.cards[quest.card_id]
    game.cards[definition.id] = replace(
        definition,
        requirement={"power": 3, "element": "Flame"},
        reward={"prestige": 5},
    )
    result = next(
        item for item in quest_previews(game, "You")
        if item["uid"] == quest.uid
    )
    assert result["ready"]
    assert result["team_power"] >= 3
    assert result["power_surplus"] == result["team_power"] - 3
    assert result["ready_after"] == (
        len(player.deployed) - len(result["dragon_uids"])
    )


def test_catalog_balance_audit_has_no_broken_definitions():
    """Catalog validation covers abilities, quests, and all 50 dragons."""
    report = catalog_audit()
    assert report["dragon_count"] == 50
    assert report["building_count"] == 18
    assert report["relic_count"] == 12
    assert report["quest_count"] == 24
    assert report["issues"] == []


def test_balance_report_contains_all_strategies():
    """Audit output stays suitable for reproducible comparisons."""
    result = balance_report(games=2, seed=60)
    assert result["simulation"]["games"] == 2
    assert set(result["simulation"]["strategies"]) == {
        "balanced", "collector", "bonding", "builder"
    }


def trade_match():
    """Start a match in the optional trade phase."""
    game = Game(["You", "Bot-A", "Bot-B"], seed=51, max_rounds=8)
    game.gather()
    game.resolve_market()
    return game


def test_bot_accepts_fair_swap_of_scarce_resource():
    """Bot can voluntarily accept an equal-valued resource exchange."""
    game = trade_match()
    game.players["You"].resources["ember"] = 10
    game.players["Bot-A"].resources.update({
        "crystal": 9, "ember": 2, "aether": 4,
    })
    trade_id = game.propose_trade(
        "You", "Bot-A",
        {"resources": {"ember": 1}},
        {"resources": {"crystal": 1}},
    )
    trade = game.trades[trade_id]
    assert bot_accepts_trade(game, "Bot-A", trade)
    game.accept_trade("Bot-A", trade_id)
    assert game.players["Bot-A"].resources["ember"] == 3
    assert game.players["Bot-A"].resources["crystal"] == 8
    assert trade_id not in game.trades


def test_bot_rejects_swap_that_worsens_resource_mix():
    """A bot does not make a trade merely because it was offered."""
    game = trade_match()
    game.players["Bot-A"].resources.update({
        "crystal": 3, "ember": 9, "aether": 4,
    })
    trade_id = game.propose_trade(
        "You", "Bot-A",
        {"resources": {"ember": 1}},
        {"resources": {"crystal": 1}},
    )
    assert not bot_accepts_trade(game, "Bot-A", game.trades[trade_id])
    game.reject_trade("Bot-A", trade_id)
    assert trade_id not in game.trades


def test_trade_phase_may_be_skipped_safely():
    """Skipping trade reaches normal actions without altering scores."""
    game = trade_match()
    scores = game.scores()
    game.begin_actions()
    assert game.phase == Phase.ACTIONS
    assert game.scores() == scores


def test_trade_phase_ui_is_optional_and_bots_do_not_leak_resources():
    """Streamlit exposes a trade phase without showing rival balances."""
    import ast
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "app.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    ui = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "trade_screen"
    )
    segment = ast.get_source_segment(source, ui)
    assert "bot_accepts_trade(" in segment
    assert "game.accept_trade(" in segment
    assert "game.reject_trade(" in segment
    assert "game.begin_actions()" in segment
    assert "game.players[bot].resources" not in segment
    assert "Phase.TRADE" in source


def test_meditation_ui_reveals_both_options():
    """Interactive choice must use two distinct game-generated instances."""
    import ast
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "app.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    ui = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "meditation_choice"
    )
    segment = ast.get_source_segment(source, ui)
    assert "game.pending_meditations[HUMAN]" in segment
    assert "game.resolve_meditation(HUMAN, index)" in segment
    assert "dragon_art_html(" in segment
    assert "portrait=True" in segment


def test_meditation_pending_prevents_deployment():
    """The game engine must not bypass a pending reveal via deployment."""
    game = ready_match()
    available = game._instance("dragon_stone_2")
    game.players["You"].reserve.append(available)
    game.offer_meditation("You")
    with pytest.raises(RuleError):
        game.deploy("You", available.uid)


def test_bot_accepts_two_ember_for_one_crystal():
    """A sufficiently attractive offer can obtain scarce Crystal."""
    game = trade_match()
    game.players["You"].resources["ember"] = 10
    game.players["Bot-A"].resources.update({
        "crystal": 2, "ember": 3, "aether": 3,
    })
    trade_id = game.propose_trade(
        "You", "Bot-A",
        {"resources": {"ember": 2}},
        {"resources": {"crystal": 1}},
    )
    trade = game.trades[trade_id]
    assert bot_accepts_trade(game, "Bot-A", trade)
    game.accept_trade("Bot-A", trade_id)
    assert game.players["You"].resources["crystal"] >= 1
    assert game.players["Bot-A"].resources["crystal"] == 1
    assert game.players["Bot-A"].resources["ember"] == 5


def test_bot_counters_one_ember_for_one_crystal():
    """Bot offers fairer quantities instead of a silent rejection."""
    game = trade_match()
    game.players["You"].resources["ember"] = 10
    game.players["Bot-A"].resources.update({
        "crystal": 2, "ember": 3, "aether": 3,
    })
    proposal = game.propose_trade(
        "You", "Bot-A",
        {"resources": {"ember": 1}},
        {"resources": {"crystal": 1}},
    )
    assert not bot_accepts_trade(
        game, "Bot-A", game.trades[proposal]
    )
    game.reject_trade("Bot-A", proposal)
    assert bot_counteroffer(
        game, "Bot-A", "You", "ember", "crystal", 1, 1
    ) == (2, 1)


def test_bot_cannot_counter_with_unavailable_crystal():
    """Counteroffers cannot promise resources the Warden does not own."""
    game = trade_match()
    game.players["Bot-A"].resources.update({
        "crystal": 0, "ember": 3, "aether": 3,
    })
    assert bot_counteroffer(
        game, "Bot-A", "You", "ember", "crystal", 1, 1
    ) is None


def test_bot_counteroffer_respects_player_supply():
    """A proposed exchange must fit the human player's inventory."""
    game = trade_match()
    game.players["You"].resources["ember"] = 1
    game.players["Bot-A"].resources.update({
        "crystal": 1, "ember": 3, "aether": 3,
    })
    assert bot_counteroffer(
        game, "Bot-A", "You", "ember", "crystal", 1, 1
    ) is None

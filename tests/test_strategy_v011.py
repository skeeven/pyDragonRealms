"""Tests for goal-directed Builder and Collector choices."""

from dataclasses import replace

from dragon_realms.bots import (
    _best_building,
    _building_value,
    choose_action,
)
from dragon_realms.engine import Game


def ready_game():
    """Create an actions-phase match with a public building market."""
    game = Game(["A", "B", "C"], seed=9, max_rounds=8)
    game.gather()
    game.resolve_market()
    game.begin_actions()
    return game


def test_builder_invests_in_early_quest_power_building():
    """Persistent quest power can outweigh a short-term quest."""
    game = ready_game()
    item = game.blueprints[0]
    card = game.cards[item.card_id]
    game.cards[card.id] = replace(
        card,
        prestige=1,
        cost={"aether": 1},
        effect="quest_power",
    )
    game.blueprints[:] = [item]
    game.quests.clear()
    assert choose_action(game, "A", "builder") == "build"
    assert item in game.players["A"].buildings


def test_builder_values_production_more_early_than_late():
    """Income becomes less useful as the match approaches its end."""
    game = ready_game()
    item = game.blueprints[0]
    card = game.cards[item.card_id]
    game.cards[card.id] = replace(
        card,
        prestige=2,
        cost={"aether": 1},
        effect="produce:crystal",
    )
    early = _building_value(game, "A", item)
    game.round = game.max_rounds
    late = _building_value(game, "A", item)
    assert early > late


def test_builder_selects_highest_valued_affordable_building():
    """Choice is based on lasting benefit, not card listing order."""
    game = ready_game()
    first, second = game.blueprints[:2]
    a = game.cards[first.card_id]
    b = game.cards[second.card_id]
    game.cards[a.id] = replace(
        a,
        prestige=1,
        cost={"aether": 1},
        effect="",
    )
    game.cards[b.id] = replace(
        b,
        prestige=2,
        cost={"aether": 1},
        effect="quest_power",
    )
    game.blueprints[:] = [first, second]
    assert _best_building(game, "A") is second


def test_collector_avoids_recruiting_into_full_team():
    """A full team converts spare Ember into bonds, not extra dragons."""
    game = ready_game()
    player = game.players["A"]
    player.deployed.extend([
        game._instance(f"dragon_stone_{i}")
        for i in range(1, 4)
    ])
    player.reserve.clear()
    game.quests.clear()
    game.blueprints.clear()
    reserve_before = len(player.reserve)
    bonds_before = sum(dragon.bond for dragon in player.deployed)
    ember_before = player.resources["ember"]

    result = choose_action(game, "A", "collector")

    assert result == "bond"
    assert len(player.reserve) == reserve_before
    assert sum(dragon.bond for dragon in player.deployed) == (
        bonds_before + 1
    )
    assert player.resources["ember"] == ember_before - 2


def test_collector_channels_if_full_team_cannot_bond():
    """Resource gathering remains legal when no scoring option exists."""
    game = ready_game()
    player = game.players["A"]
    player.deployed.extend([
        game._instance(f"dragon_stone_{i}")
        for i in range(1, 4)
    ])
    game.quests.clear()
    game.blueprints.clear()
    player.resources["ember"] = 0
    reserve_before = len(player.reserve)

    assert choose_action(game, "A", "collector") == "channel"
    assert len(player.reserve) == reserve_before

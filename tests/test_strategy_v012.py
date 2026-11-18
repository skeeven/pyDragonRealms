"""Tests for v0.12 adaptive AI and simulation diagnostics."""

from dataclasses import replace

from dragon_realms.bots import _building_value, choose_action
from dragon_realms.engine import Game
from dragon_realms.simulate import play_game, simulate


def ready_game():
    """Build a game ready for automated action decisions."""
    game = Game(["A", "B", "C"], seed=12, max_rounds=8)
    game.gather()
    game.resolve_market()
    game.begin_actions()
    return game


def test_builder_bonds_when_other_scoring_actions_unavailable():
    """Builder can strengthen its dragons rather than only channel."""
    game = ready_game()
    game.quests.clear()
    game.blueprints.clear()
    player = game.players["A"]
    before = [dragon.bond for dragon in player.deployed]
    assert choose_action(game, "A", "builder") == "bond"
    assert sum(dragon.bond for dragon in player.deployed) == (
        sum(before) + 1
    )


def test_second_quest_power_building_has_no_duplicate_future_bonus():
    """Only the first Quest Beacon affects the engine's quest power."""
    game = ready_game()
    player = game.players["A"]
    first = game.blueprints[0]
    second = game.blueprints[1]
    card_a = game.cards[first.card_id]
    card_b = game.cards[second.card_id]
    game.cards[card_a.id] = replace(
        card_a, effect="quest_power", cost={"aether": 1},
        prestige=2,
    )
    game.cards[card_b.id] = replace(
        card_b, effect="quest_power", cost={"aether": 1},
        prestige=2,
    )
    initial = _building_value(game, "A", second)
    player.buildings.append(first)
    repeated = _building_value(game, "A", second)
    assert repeated < initial


def test_average_action_counts_match_eight_round_action_budget():
    """Each computer player spends two actions in every round."""
    report = simulate(games=4, players=4, seed=20, rounds=8)
    for strategy in report["strategies"].values():
        action_counts = strategy["average_actions"]
        assert set(action_counts) == {
            "quest", "build", "bond", "channel",
            "recruit", "meditate",
        }
        assert sum(action_counts.values()) == 16


def test_action_report_reflects_actual_engine_events():
    """Reported action categories come directly from logged events."""
    result = play_game(players=4, seed=33, rounds=8)
    actions = [
        event for event in result.events
        if event["event"] == "action"
    ]
    assert len(actions) == 64
    assert all(
        event["action"] in {
            "quest", "build", "bond", "channel",
            "recruit", "meditate",
        }
        for event in actions
    )

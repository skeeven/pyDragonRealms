"""Regression tests for v0.10 opponent decisions and match length."""

from dragon_realms.engine import Game
from dragon_realms.bots import deploy_best
from dragon_realms.simulate import _bid, play_game, simulate
from random import Random


def test_eight_round_match_finishes():
    """The simulator supports the Streamlit default match length."""
    result = play_game(players=4, seed=11, rounds=8)
    assert result.events[-1]["event"] == "finished"
    assert len(result.scores) == 4
    assert all(sum(result.breakdowns[pid].values()) == score
               for pid, score in result.scores.items())


def test_eight_round_statistics():
    """The report identifies the correct match length."""
    report = simulate(games=4, players=4, seed=3, rounds=8)
    assert report["rounds"] == 8
    assert report["games"] == 4
    assert sum(
        item["wins"] for item in report["strategies"].values()
    ) == 4


def test_bid_is_affordable_and_uses_available_market_cards():
    """Market ranking never commits more Crystal than a bot owns."""
    game = Game(["A", "B", "C"], seed=3, max_rounds=8)
    game.gather()
    _bid(game, "A", "collector", Random(17))
    bids = game.bids["A"]
    assert len(bids) <= 2
    assert sum(bids.values()) <= game.players["A"].resources["crystal"]
    assert set(bids).issubset({item.uid for item in game.market})


def test_deployment_picks_useful_dragon_and_is_not_repeated():
    """The bot should fill its team without spending an action."""
    game = Game(["A", "B", "C"], seed=3)
    game.gather()
    game.resolve_market()
    game.begin_actions()
    player = game.players["A"]
    before_actions = player.actions_left
    player.reserve.append(game._instance("dragon_stone_1"))
    deploy_best(game, "A")
    assert player.swapped
    assert len(player.deployed) == 3
    assert not player.reserve
    assert player.actions_left == before_actions
    deploy_best(game, "A")
    assert len(player.deployed) == 3


def test_bot_team_swap_keeps_engine_state_consistent():
    """Evaluating possible replacements must not duplicate cards."""
    game = Game(["A", "B", "C"], seed=3)
    game.gather()
    game.resolve_market()
    game.begin_actions()
    player = game.players["A"]
    player.deployed.extend([
        game._instance("dragon_stone_1"),
        game._instance("dragon_stone_2"),
        game._instance("dragon_stone_3"),
    ])
    player.reserve.append(game._instance("dragon_shadow_8"))
    ids_before = {
        item.uid for item in player.deployed + player.reserve
    }
    deploy_best(game, "A")
    ids_after = {
        item.uid for item in player.deployed + player.reserve
    }
    assert ids_before == ids_after
    assert len(player.deployed) == 5
    assert len(player.reserve) == 1

"""v0.3 integration tests for quest-aware automated players."""
import pytest

from dragon_realms.bots import quest_options, score_breakdown
from dragon_realms.engine import Game, Phase
from dragon_realms.simulate import play_game, simulate


@pytest.mark.parametrize("players", [3, 4, 5, 6])
def test_score_components_match_engine(players):
    result = play_game(players=players, seed=23)
    for pid, score in result.scores.items():
        assert sum(result.breakdowns[pid].values()) == score


def test_quest_options_does_not_mutate_state():
    game = Game(["a", "b", "c"], seed=5)
    game.gather()
    before = game.version
    list(quest_options(game, "a"))
    assert game.version == before


def test_rotation_counts_for_five_players():
    report = simulate(games=8, players=5, seed=9)
    assert sum(s["appearances"] for s in
               report["strategies"].values()) == 40
    assert sum(s["wins"] for s in report["strategies"].values()) == 8


def test_complete_matches_still_finish():
    for seed in range(10):
        result = play_game(4, seed)
        assert result.events[-1]["event"] == "finished"

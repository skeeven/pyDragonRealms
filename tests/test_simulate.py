"""Integration checks for the automated simulation layer."""
import pytest

from dragon_realms.simulate import STRATEGIES, play_game, simulate


@pytest.mark.parametrize("players", [3, 4, 5, 6])
def test_complete_match(players):
    result = play_game(players=players, seed=17)
    assert len(result.scores) == players
    assert result.winners
    assert all(pid in result.scores for pid in result.winners)
    assert result.events[-1]["event"] == "finished"


def test_reproducible_scores():
    a = play_game(players=4, seed=19)
    b = play_game(players=4, seed=19)
    assert a.scores == b.scores
    assert a.winners == b.winners


def test_aggregate_statistics():
    report = simulate(games=5, players=4, seed=4)
    assert report["games"] == 5
    assert set(report["strategies"]) == set(STRATEGIES)
    assert sum(item["wins"] for item in report["strategies"].values()) == 5


def test_invalid_inputs():
    with pytest.raises(ValueError):
        play_game(players=2)
    with pytest.raises(ValueError):
        simulate(games=0)
    with pytest.raises(ValueError):
        play_game(players=4, strategies=("balanced",))

"""Regression tests for configurable match length."""

import pytest

from dragon_realms import Game, Phase, RuleError


@pytest.mark.parametrize("rounds", [6, 8, 10])
def test_configurable_match_length(rounds):
    """A match should finish at its configured round limit."""
    game = Game(["alice", "bob", "cara"], seed=13, max_rounds=rounds)
    for expected_round in range(1, rounds + 1):
        assert game.round == expected_round
        game.gather()
        game.resolve_market()
        game.begin_actions()
        game.end_round()
        expected = (Phase.FINISHED if expected_round == rounds
                    else Phase.GATHER)
        assert game.phase == expected


def test_invalid_round_limit():
    """Reject unsupported game lengths."""
    with pytest.raises(RuleError):
        Game(["alice", "bob", "cara"], max_rounds=2)
    with pytest.raises(RuleError):
        Game(["alice", "bob", "cara"], max_rounds=13)

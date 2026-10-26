"""Smoke tests for the interactive command-line game."""
from dragon_realms.engine import Phase
from dragon_realms.play import choose, play


def test_choose_retries_invalid_entries():
    answers = iter(["oops", "-1", "2"])
    assert choose("Choice: ", 3, input_fn=lambda _: next(answers)) == 2


def test_full_terminal_game_with_scripted_input(capsys):
    def scripted(prompt):
        if prompt.startswith("Bid"):
            return "0"
        if prompt.startswith("Reserve dragon"):
            return "0"
        if prompt.startswith("Action:"):
            return "1"
        if prompt.startswith("Resource"):
            return "1"
        return "0"

    game = play(seed=3, tutorial=False, input_fn=scripted)
    assert game.phase == Phase.FINISHED
    assert len(game.scores()) == 4
    assert "FINAL RESULTS" in capsys.readouterr().out

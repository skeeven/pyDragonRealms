"""Round-trip and validation coverage for portable Dragon Realms saves."""

import json
from random import Random

import pytest

from dragon_realms.engine import Game, Phase
from dragon_realms.savegame import (
    export_game,
    export_session,
    import_game,
    import_session,
)


def make_match():
    """Create a regular eight-round match."""
    return Game(["You", "Bot-Collector", "Bot-Bonding", "Bot-Builder"],
                seed=13, max_rounds=8)


def to_actions(game):
    """Advance a match to the decision phase."""
    game.gather()
    game.resolve_market()
    game.begin_actions()


@pytest.mark.parametrize("phase", ["gather", "market", "actions"])
def test_game_round_trip_preserves_state(phase):
    """Saved matches restore scores, zones, and the current phase."""
    game = make_match()
    if phase in {"market", "actions"}:
        game.gather()
    if phase == "actions":
        game.resolve_market()
        game.begin_actions()
        game.act("You", "channel", gains={"crystal": 2})
        game.players["You"].reserve.append(
            game._instance("dragon_stone_1")
        )
    restored = import_game(export_game(game))
    assert restored.phase == game.phase
    assert restored.round == game.round
    assert restored.max_rounds == game.max_rounds
    assert restored.order == game.order
    assert restored.scores() == game.scores()
    assert restored.view("You") == game.view("You")
    assert restored.decks == game.decks
    assert restored.events == game.events


def test_save_and_resume_can_continue_round():
    """Continue playing a restored match with its original actions."""
    game = make_match()
    to_actions(game)
    game.act("You", "channel", gains={"crystal": 2})
    restored = import_game(export_game(game))
    assert restored.players["You"].actions_left == 1
    restored.act("You", "channel", gains={"ember": 2})
    assert restored.players["You"].actions_left == 0
    restored.end_round()
    assert restored.phase == Phase.GATHER
    assert restored.round == 2


def test_session_round_trip_keeps_bot_rng_and_history():
    """Bidding choices stay reproducible across a save/resume."""
    game = make_match()
    game.gather()
    bot_rng = Random(42)
    bot_rng.random()
    auction = [{"winner": "You", "card": "Flame Wyrm",
                "amount": 3}]
    restored, rng, history = import_session(
        export_session(game, bot_rng, auction)
    )
    assert restored.phase == Phase.MARKET
    assert history == auction
    assert rng.random() == bot_rng.random()


def test_round_trip_after_game_finished():
    """A finished game can be restored to its final scoreboard."""
    game = make_match()
    for _ in range(game.max_rounds):
        to_actions(game)
        game.end_round()
    restored = import_game(export_game(game))
    assert restored.phase == Phase.FINISHED
    assert list(restored.players) == list(game.players)
    assert restored.order == game.order
    assert restored.winners() == game.winners()
    assert restored.scores() == game.scores()


def test_restored_tied_winners_keep_original_player_order():
    """Turn priority must not reorder tied winners on load."""
    game = make_match()
    for _ in range(game.max_rounds):
        to_actions(game)
        game.end_round()

    assert len(game.winners()) == len(game.players)
    restored = import_game(export_game(game))
    assert restored.winners() == game.winners()
    assert list(restored.players) == list(game.players)
    assert restored.order == game.order


def test_reject_invalid_json_and_wrong_version():
    """Uploaded files must use the recognized save format."""
    with pytest.raises(ValueError):
        import_game("not-json")
    with pytest.raises(ValueError):
        import_game("{}")
    data = json.loads(export_game(make_match()))
    data["version"] = 999
    with pytest.raises(ValueError):
        import_game(json.dumps(data))


def test_reject_duplicate_cards_and_invalid_bonds():
    """Invalid card zones must not enter active game state."""
    game = make_match()
    data = json.loads(export_game(game))
    dragon = data["players"]["You"]["deployed"][0]
    data["players"]["You"]["reserve"].append(dict(dragon))
    with pytest.raises(ValueError, match="Duplicate"):
        import_game(json.dumps(data))
    data["players"]["You"]["reserve"].clear()
    data["players"]["You"]["deployed"][0]["bond"] = 99
    with pytest.raises(ValueError):
        import_game(json.dumps(data))


def test_reject_oversized_and_malformed_session():
    """Untrusted uploads have a size limit and validation checks."""
    with pytest.raises(ValueError, match="too large"):
        import_session(b"x" * 1_000_001)
    data = json.loads(
        export_session(make_match(), Random(1), [])
    )
    data["auction"] = ["invalid"]
    with pytest.raises(ValueError):
        import_session(json.dumps(data))

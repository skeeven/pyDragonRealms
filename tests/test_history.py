"""Tests for v0.14 final standings and game-history highlights."""

from dragon_realms.engine import Game, Phase
from dragon_realms.history import leaderboard, match_history
from dragon_realms.savegame import export_game, import_game


def game_at_actions():
    """Prepare a regular round-one match for action testing."""
    game = Game(["A", "B", "C"], seed=5, max_rounds=3)
    game.gather()
    game.resolve_market()
    game.begin_actions()
    return game


def test_leaderboard_matches_engine_scores_and_ties():
    """All tied Wardens keep the same competition rank."""
    game = game_at_actions()
    standings = leaderboard(game)
    assert len(standings) == 3
    assert all(item["rank"] == 1 for item in standings)
    assert [item["warden"] for item in standings] == list(game.players)
    assert all(item["total"] == game.score(item["warden"])
               for item in standings)


def test_leaderboard_uses_engine_tiebreakers():
    """Completed quests break equal-prestige ties."""
    game = game_at_actions()
    game.players["B"].quest_prestige = 1
    game.players["A"].quest_prestige = 1
    game.players["B"].quests_completed = 1
    standings = leaderboard(game)
    assert standings[0]["warden"] == "B"
    assert standings[0]["rank"] == 1
    assert standings[1]["rank"] == 2
    assert standings[2]["rank"] == 3


def test_match_history_tracks_descriptive_actions_and_rounds():
    """History shows the recorded action type and useful context."""
    game = game_at_actions()
    game.act("A", "bond", uid=game.players["A"].deployed[0].uid)
    game.act("A", "channel", gains={"crystal": 2})
    history = match_history(game)
    assert any("bonded with Starter" in row["event"] for row in history)
    assert all(row["round"] == 1 for row in history)
    game.end_round()
    assert game.phase == Phase.GATHER
    game.gather()
    assert any(row["round"] == 1 for row in match_history(game))


def test_history_survives_save_restore():
    """Victory history continues to work after portable JSON loading."""
    game = game_at_actions()
    game.act("A", "bond", uid=game.players["A"].deployed[0].uid)
    original = match_history(game)
    restored = import_game(export_game(game))
    assert match_history(restored) == original
    assert leaderboard(restored) == leaderboard(game)


def test_history_supports_older_unnamed_events():
    """Existing save files without metadata remain displayable."""
    game = game_at_actions()
    game.events = [
        {
            "event": "auction_won", "player": "B",
            "card": "legacy-uid", "amount": 3,
        },
        {
            "event": "action", "player": "A",
            "action": "quest",
        },
        {
            "event": "round_started", "round": 2,
        },
        {
            "event": "deployed", "player": "C",
            "card": "legacy-dragon",
        },
    ]
    history = match_history(game)
    assert len(history) == 3
    assert history[0]["round"] == 1
    assert history[-1]["round"] == 2
    assert "market card" in history[0]["event"]
    assert "completed a quest" in history[1]["event"]

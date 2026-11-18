"""Tests for non-mutating Dragon Realms strategic guidance."""

from dataclasses import replace

from dragon_realms.advisor import (
    chapter,
    quest_previews,
    recommendation,
)
from dragon_realms.engine import Game


def make_game():
    """Return a match ready for human decisions."""
    game = Game(["You", "Bot-A", "Bot-B"], seed=7, max_rounds=8)
    game.gather()
    game.resolve_market()
    game.begin_actions()
    return game


def test_quest_previews_do_not_change_game_state():
    """Viewing recommendations cannot spend actions or resources."""
    game = make_game()
    player = game.players["You"]
    before = (
        game.version,
        dict(player.resources),
        player.actions_left,
        [dragon.exhausted for dragon in player.deployed],
        game.score("You"),
    )
    first = quest_previews(game, "You")
    second = quest_previews(game, "You")
    assert first == second
    assert len(first) == len(game.quests)
    assert before == (
        game.version,
        dict(player.resources),
        player.actions_left,
        [dragon.exhausted for dragon in player.deployed],
        game.score("You"),
    )


def test_ready_quest_has_valid_team():
    """An offered quest can be completed with the suggested dragons."""
    game = make_game()
    quest = game.quests[0]
    card = game.cards[quest.card_id]
    game.cards[card.id] = replace(
        card,
        requirement={"power": 1},
        reward={"prestige": 5},
    )
    preview = next(
        item for item in quest_previews(game, "You")
        if item["uid"] == quest.uid
    )
    assert preview["ready"]
    assert len(preview["dragon_uids"]) == 1
    assert preview["prestige"] == 5
    assert recommendation(game, "You")["kind"] == "quest"
    game.act(
        "You", "quest",
        uid=preview["uid"],
        dragons=preview["dragon_uids"],
    )
    assert game.players["You"].quest_prestige == 5
    assert game.players["You"].actions_left == 1


def test_unavailable_quest_explains_missing_requirements():
    """Quest guidance identifies missing power and elements."""
    game = make_game()
    quest = game.quests[0]
    card = game.cards[quest.card_id]
    game.cards[card.id] = replace(
        card,
        requirement={
            "power": 99,
            "element": "Shadow",
            "distinct": 3,
        },
    )
    preview = next(
        item for item in quest_previews(game, "You")
        if item["uid"] == quest.uid
    )
    assert not preview["ready"]
    reason = " ".join(preview["reasons"])
    assert "99" in reason
    assert "Shadow" in reason
    assert "different elements" in reason


def test_game_stage_guidance():
    """Game plan changes at appropriate stages."""
    game = make_game()
    assert "Early game" in chapter(game)
    game.round = 4
    assert "Midgame" in chapter(game)
    game.round = 8
    assert "Endgame" in chapter(game)

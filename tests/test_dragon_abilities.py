"""Tests for the six distinct nonstarter dragon abilities."""

from dataclasses import replace

from dragon_realms import Game
from dragon_realms.advisor import quest_previews
from dragon_realms.bots import quest_options, score_breakdown


def match_with(element: str):
    """Prepare a match with one nonstarter dragon of an element."""
    game = Game(["You", "Bot-A", "Bot-B"], seed=7)
    player = game.players["You"]
    dragon = game._instance(f"dragon_{element.lower()}_1")
    player.deployed = [dragon]
    game.gather()
    game.resolve_market()
    game.begin_actions()
    return game, dragon


def make_easy_quest(game, element: str, power: int,
                    prestige: int = 4):
    """Replace a public quest requirement for deterministic tests."""
    item = game.quests[0]
    card = game.cards[item.card_id]
    game.cards[card.id] = replace(
        card,
        requirement={"power": power, "element": element},
        reward={"prestige": prestige},
    )
    return item


def test_resource_dragons_produce_different_resources():
    """Flame, Tide and Grove provide their respective income."""
    for element, resource in (
        ("Flame", "ember"),
        ("Tide", "crystal"),
        ("Grove", "aether"),
    ):
        game, _ = match_with(element)
        player = game.players["You"]
        expected = {
            "crystal": 7,
            "ember": 3,
            "aether": 3,
        }
        expected[resource] += 1
        assert player.resources == expected


def test_storm_adds_quest_power_without_changing_base_power():
    """Storm can meet a quest one point above printed power."""
    game, dragon = match_with("Storm")
    quest = make_easy_quest(game, "Storm", power=2)
    assert game.cards[dragon.card_id].power == 1
    options = list(quest_options(game, "You"))
    assert any(item.uid == quest.uid for item, _, _ in options)
    previews = quest_previews(game, "You")
    assert next(
        item for item in previews if item["uid"] == quest.uid
    )["ready"]
    game.act("You", "quest", uid=quest.uid,
             dragons=[dragon.uid])
    assert game.players["You"].quest_prestige == 4


def test_stone_adds_one_passive_prestige():
    """Stone scores an extra point when deployed."""
    game, dragon = match_with("Stone")
    card = game.cards[dragon.card_id]
    assert game.score("You") == card.prestige + 1
    assert score_breakdown(game, "You")["dragons"] == (
        card.prestige + 1
    )


def test_shadow_bonus_applies_to_quest_rewards():
    """Shadow quest bonuses appear in previews and actual scoring."""
    game, dragon = match_with("Shadow")
    quest = make_easy_quest(game, "Shadow", power=1, prestige=4)
    options = list(quest_options(game, "You"))
    expected = next(
        reward for item, _, reward in options if item.uid == quest.uid
    )
    assert expected == 5
    preview = next(
        item for item in quest_previews(game, "You")
        if item["uid"] == quest.uid
    )
    assert preview["prestige"] == 5
    game.act("You", "quest", uid=quest.uid,
             dragons=[dragon.uid])
    assert game.players["You"].quest_prestige == 5


def test_starter_dragons_do_not_have_abilities():
    """Free starter dragons do not produce or get bonus power."""
    game = Game(["You", "Bot-A", "Bot-B"], seed=7)
    starters = game.players["You"].deployed
    assert all(not game.cards[d.card_id].effect for d in starters)
    game.gather()
    assert game.players["You"].resources == {
        "crystal": 7,
        "ember": 3,
        "aether": 3,
    }

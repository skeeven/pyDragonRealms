"""v0.28 signature dragon ability and scoring regression tests."""

from dataclasses import replace

import pytest

from dragon_realms.advisor import quest_previews
from dragon_realms.bots import quest_options, score_breakdown
from dragon_realms.engine import Game, RuleError, make_catalog
from dragon_realms.savegame import export_game, import_game


SIGNATURES = {
    "dragon_flame_7": "flame_focus",
    "dragon_tide_7": "tide_bounty",
    "dragon_grove_8": "grove_bounty",
}


def ready_match(card_id):
    """Prepare a legal match with one signature dragon deployed."""
    game = Game(["You", "Bot-A", "Bot-B"], seed=17, max_rounds=8)
    game.players["You"].deployed.append(game._instance(card_id))
    game.gather()
    game.resolve_market()
    game.begin_actions()
    return game


def easy_quest(game, element, power=1):
    """Make the first public quest deterministic for ability tests."""
    item = game.quests[0]
    card = game.cards[item.card_id]
    game.cards[card.id] = replace(
        card,
        requirement={"power": power, "element": element},
        reward={"prestige": 3},
    )
    return item


def test_three_signature_cards_keep_stable_ids_and_names():
    """Only the named dragons gain unique new ability descriptions."""
    catalog = make_catalog()
    expected_names = {
        "dragon_flame_7": "Kindlefang",
        "dragon_tide_7": "Foamwing",
        "dragon_grove_8": "Wildbloom",
    }
    for card_id, effect in SIGNATURES.items():
        assert catalog[card_id].effect == effect
        assert catalog[card_id].name == expected_names[card_id]
    assert catalog["dragon_flame_1"].effect == "produce:ember"
    assert catalog["dragon_tide_1"].effect == "produce:crystal"
    assert catalog["dragon_grove_1"].effect == "produce:aether"


def test_kindlefang_power_matches_engine_bots_and_advisor():
    """Kindlefang's extra two power qualifies a real quest."""
    game = ready_match("dragon_flame_7")
    dragon = game.players["You"].deployed[-1]
    printed = game.cards[dragon.card_id].power
    quest = easy_quest(game, "Flame", power=printed + 2)
    options = list(quest_options(game, "You"))
    assert any(item.uid == quest.uid for item, _, _ in options)
    preview = next(
        item for item in quest_previews(game, "You")
        if item["uid"] == quest.uid
    )
    assert preview["ready"]
    game.act(
        "You", "quest", uid=quest.uid, dragons=[dragon.uid],
    )
    assert game.players["You"].quest_prestige == 3
    assert dragon.exhausted


@pytest.mark.parametrize(
    ("card_id", "element", "resource"),
    [
        ("dragon_tide_7", "Tide", "crystal"),
        ("dragon_grove_8", "Grove", "aether"),
    ],
)
def test_signature_quest_bounty_adds_one_resource(
    card_id, element, resource
):
    """Bounty triggers only when its dragon completes a quest."""
    game = ready_match(card_id)
    player = game.players["You"]
    dragon = player.deployed[-1]
    quest = easy_quest(game, element)
    before = dict(player.resources)
    game.act(
        "You", "quest", uid=quest.uid, dragons=[dragon.uid],
    )
    assert player.resources[resource] == before[resource] + 1
    assert player.quest_prestige == 3
    assert score_breakdown(game, "You")["quests"] == 3


def test_quest_bounty_requires_signature_dragon_on_team():
    """A deployed but unused bounty dragon grants no resource."""
    game = ready_match("dragon_tide_7")
    player = game.players["You"]
    quest = easy_quest(game, "Flame")
    starter = next(
        dragon for dragon in player.deployed
        if dragon.card_id == "starter_flame"
    )
    crystal_before = player.resources["crystal"]
    game.act(
        "You", "quest", uid=quest.uid, dragons=[starter.uid],
    )
    assert player.resources["crystal"] == crystal_before


def test_quest_advisor_shows_signature_bounty_reward():
    """The suggested Wildbloom team includes the extra Aether reward."""
    game = ready_match("dragon_grove_8")
    quest = easy_quest(game, "Grove")
    preview = next(
        item for item in quest_previews(game, "You")
        if item["uid"] == quest.uid
    )
    assert preview["ready"]
    assert preview["reward"]["aether"] == 1
    assert any(
        item.uid in preview["dragon_uids"]
        for item in game.players["You"].deployed
        if item.card_id == "dragon_grove_8"
    )


def test_bounty_respects_resource_cap():
    """Bounty cannot push a resource above the normal cap."""
    game = ready_match("dragon_tide_7")
    player = game.players["You"]
    player.resources["crystal"] = 20
    dragon = player.deployed[-1]
    quest = easy_quest(game, "Tide")
    game.act(
        "You", "quest", uid=quest.uid, dragons=[dragon.uid],
    )
    assert player.resources["crystal"] == 20


def test_signature_dragon_save_round_trip():
    """Original IDs and their new abilities survive old-format JSON."""
    game = ready_match("dragon_grove_8")
    restored = import_game(export_game(game))
    assert restored.cards["dragon_grove_8"].effect == "grove_bounty"
    assert (
        restored.players["You"].deployed[-1].card_id
        == "dragon_grove_8"
    )


def test_invalid_quest_cannot_collect_bounty():
    """Failed quests must never grant bonus resources."""
    game = ready_match("dragon_tide_7")
    player = game.players["You"]
    dragon = player.deployed[-1]
    quest = easy_quest(game, "Tide", power=99)
    before = dict(player.resources)
    with pytest.raises(RuleError):
        game.act(
            "You", "quest", uid=quest.uid, dragons=[dragon.uid],
        )
    assert player.resources == before
    assert player.actions_left == 2

"""Tests for v0.17 unique dragon identities and collection progress."""

from random import Random
from xml.etree import ElementTree

from dragon_realms.artwork import dragon_svg
from dragon_realms.codex import (
    codex_entries,
    codex_summary,
    discovered_dragons,
)
from dragon_realms.dragon_identity import (
    DRAGON_NAMES,
    dragon_lore,
    dragon_variant,
)
from dragon_realms.engine import ELEMENTS, Game, make_catalog
from dragon_realms.savegame import export_game, import_game


def game_at_actions():
    """Create a game in the phase where recruiting is allowed."""
    game = Game(["You", "Bot-A", "Bot-B"], seed=9)
    game.gather()
    game.resolve_market()
    game.begin_actions()
    return game


def test_all_48_dragons_have_unique_names_and_stable_ids():
    """Naming upgrades preserve the original card identifiers and stats."""
    catalog = make_catalog()
    ids = [
        f"dragon_{element.lower()}_{number}"
        for element in ELEMENTS
        for number in range(1, 9)
    ]
    names = [catalog[card_id].name for card_id in ids]
    assert len(set(names)) == 48
    assert len(DRAGON_NAMES) == 6
    assert all(names)
    assert catalog["starter_flame"].name == "Starter Flame"
    assert catalog["starter_tide"].name == "Starter Tide"
    assert catalog["dragon_storm_8"].power == 3
    assert catalog["dragon_storm_8"].effect == "storm_boost"


def test_dragon_lore_and_variants_are_deterministic():
    """Individual identities are consistent across repeated calls."""
    for element in ELEMENTS:
        for index in range(1, 9):
            card_id = f"dragon_{element.lower()}_{index}"
            assert dragon_variant(card_id) == index
            assert make_catalog()[card_id].name in dragon_lore(card_id)
    assert dragon_variant("starter_flame") == 0


def test_all_dragon_artwork_variations_are_valid_and_unique():
    """Eight dragon variants per element remain valid accessible SVG."""
    for element in ELEMENTS:
        art = [dragon_svg(element, 112, i) for i in range(1, 9)]
        assert len(set(art)) == 8
        for variant, svg in enumerate(art, start=1):
            root = ElementTree.fromstring(svg)
            assert root.tag.endswith("svg")
            assert f"{element.lower()}-{variant}" in svg


def test_codex_initially_hides_all_nonstarter_dragons():
    """Starter cards aren't counted as collectibles."""
    game = game_at_actions()
    entries = codex_entries(game, "You")
    assert len(entries) == 48
    assert all(item["status"] == "Unknown" for item in entries)
    assert all(item["name"] == "Undiscovered" for item in entries)
    assert codex_summary(game, "You") == {
        "discovered": 0, "owned": 0, "total": 48,
    }


def test_owned_dragon_is_discovered_and_has_lore():
    """A recruited dragon appears as an owned Codex entry."""
    game = game_at_actions()
    player = game.players["You"]
    dragon = game._instance("dragon_stone_3")
    player.reserve.append(dragon)
    entry = next(
        item for item in codex_entries(game, "You", "Stone")
        if item["card_id"] == dragon.card_id
    )
    assert entry["status"] == "Owned"
    assert entry["name"] == "Boulderspine"
    assert "Boulderspine" in entry["lore"]


def test_past_acquisition_remains_discovered_after_card_is_lost():
    """Acquisition history tracks discoveries beyond current ownership."""
    game = game_at_actions()
    card_id = "dragon_flame_2"
    game.events.append({
        "event": "auction_won", "player": "You",
        "card_id": card_id, "round": 1,
    })
    assert card_id in discovered_dragons(game, "You")
    entry = next(
        item for item in codex_entries(game, "You", "Flame")
        if item["card_id"] == card_id
    )
    assert entry["status"] == "Discovered"
    assert codex_summary(game, "You")["owned"] == 0


def test_recruitment_is_recorded_for_collection_and_restored():
    """New event metadata is carried in the existing JSON save format."""
    game = game_at_actions()
    player = game.players["You"]
    # Recruit is affordable with the regular gather resources.
    target = game.decks["dragon"][-1]
    player.resources["crystal"] = 20
    game.act("You", "recruit")
    assert target in discovered_dragons(game, "You")
    assert game.events[-1]["acquired_dragon_id"] == target
    restored = import_game(export_game(game))
    assert discovered_dragons(restored, "You") == (
        discovered_dragons(game, "You")
    )


def test_codex_does_not_modify_engine_state():
    """Collection browsing is read-only."""
    game = game_at_actions()
    version = game.version
    before = game.scores()
    codex_entries(game, "You", "Tide")
    codex_summary(game, "You")
    assert game.version == version
    assert game.scores() == before

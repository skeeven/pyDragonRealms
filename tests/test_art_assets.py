"""Tests for the optional v0.19 illustrated dragon art assets."""

import base64
from pathlib import Path

import pytest

from dragon_realms import art_assets
from dragon_realms.art_assets import dragon_art_html, dragon_art_path
from dragon_realms.artwork import dragon_svg


def test_registry_contains_thirty_nine_illustrated_dragons():
    """Registered assets map to 39 canonical IDs and thumbnail paths."""
    from dragon_realms.engine import make_catalog

    catalog = make_catalog()
    expected_batch = {
        "dragon_flame_6": "flame/blazehorn.webp",
        "dragon_flame_7": "flame/kindlefang.webp",
        "dragon_tide_5": "tide/wavecaller.webp",
        "dragon_tide_7": "tide/foamwing.webp",
        "dragon_grove_6": "grove/bloomtail.webp",
        "dragon_storm_5": "storm/skyshiver.webp",
        "dragon_stone_5": "stone/cragheart.webp",
        "dragon_shadow_5": "shadow/echofang.webp",
    }
    assert len(art_assets.DRAGON_ART) == 39
    assert len(art_assets.DRAGON_THUMBNAILS) == 39
    assert {
        card_id: art_assets.DRAGON_ART[card_id]
        for card_id in expected_batch
    } == expected_batch
    for card_id, portrait in art_assets.DRAGON_ART.items():
        assert card_id in catalog
        assert portrait.endswith(".webp")
        assert art_assets.DRAGON_THUMBNAILS[card_id] == (
            portrait.replace(".webp", "-thumb.webp")
        )


def test_missing_art_uses_original_svg(tmp_path, monkeypatch):
    """Registered dragons use SVG when their image files are absent."""
    monkeypatch.setattr(art_assets, "ASSET_ROOT", tmp_path)
    assert dragon_art_html("dragon_flame_5", "Flame", 80) == (
        dragon_svg("Flame", 80, 5)
    )


def test_unillustrated_dragon_uses_svg_even_with_art_installed():
    """Unregistered dragons always retain their original SVG fallback."""
    assert "dragon_shadow_8" not in art_assets.DRAGON_ART
    assert dragon_art_html("dragon_shadow_8", "Shadow", 80) == (
        dragon_svg("Shadow", 80, 8)
    )


def test_missing_showcase_art_still_works(tmp_path, monkeypatch):
    """Missing image files never break the app or Codex."""
    monkeypatch.setattr(art_assets, "ASSET_ROOT", tmp_path)
    assert dragon_art_path("dragon_stone_1") is None
    assert dragon_art_html("dragon_stone_1", "Stone", 112) == (
        dragon_svg("Stone", 112, 1)
    )


def test_valid_local_webp_renders_as_image(tmp_path, monkeypatch):
    """An existing asset wins over SVG and uses encoded image bytes."""
    monkeypatch.setattr(art_assets, "ASSET_ROOT", tmp_path)
    file_path = tmp_path / "stone" / "granitehide.webp"
    file_path.parent.mkdir()
    content = b"RIFFxxxxWEBPexample"
    file_path.write_bytes(content)
    artwork = dragon_art_html("dragon_stone_1", "Stone", 90)
    assert "<img " in artwork
    assert "data:image/webp;base64," in artwork
    assert base64.b64encode(content).decode("ascii") in artwork
    assert 'width="90"' in artwork
    assert 'alt="Stone dragon illustration"' in artwork


def test_oversized_image_is_ignored(tmp_path, monkeypatch):
    """Excessively large files safely use the SVG fallback."""
    monkeypatch.setattr(art_assets, "ASSET_ROOT", tmp_path)
    file_path = tmp_path / "stone" / "granitehide.webp"
    file_path.parent.mkdir()
    file_path.write_bytes(b"x" * 12)
    monkeypatch.setattr(art_assets, "MAX_ART_BYTES", 10)
    assert dragon_art_path("dragon_stone_1") is None
    assert "<svg " in dragon_art_html(
        "dragon_stone_1", "Stone", 80
    )


@pytest.mark.parametrize("bad_size", [0, 19, 513, True, 5.5])
def test_invalid_illustration_size_is_rejected(bad_size):
    """Invalid sizes cannot bypass validated SVG or HTML rendering."""
    with pytest.raises(ValueError):
        dragon_art_html("dragon_stone_1", "Stone", bad_size)


def test_artwork_html_does_not_mutate_gameplay():
    """Changing artwork is completely independent of game state."""
    from dragon_realms.engine import Game

    game = Game(["You", "Bot-A", "Bot-B"], seed=7)
    score = game.scores()
    dragon_art_html("dragon_stone_1", "Stone", 80)
    assert game.scores() == score


def test_thumbnail_and_portrait_resolve_separately(
    tmp_path, monkeypatch
):
    """Card crops and full Codex portraits use different image files."""
    monkeypatch.setattr(art_assets, "ASSET_ROOT", tmp_path)
    folder = tmp_path / "stone"
    folder.mkdir()
    (folder / "granitehide-thumb.webp").write_bytes(b"THUMB")
    (folder / "granitehide.webp").write_bytes(b"PORTRAIT")

    thumbnail = dragon_art_html("dragon_stone_1", "Stone", 90)
    portrait = dragon_art_html(
        "dragon_stone_1", "Stone", 240, portrait=True
    )
    assert base64.b64encode(b"THUMB").decode("ascii") in thumbnail
    assert base64.b64encode(b"PORTRAIT").decode("ascii") in portrait
    assert "object-fit:cover" in thumbnail
    assert "object-fit:contain" in portrait
    assert 'height="90"' in thumbnail
    assert 'height="240"' not in portrait


def test_old_artwork_pack_without_thumbnail_still_works(
    tmp_path, monkeypatch
):
    """Existing v0.19 portrait assets remain backward compatible."""
    monkeypatch.setattr(art_assets, "ASSET_ROOT", tmp_path)
    folder = tmp_path / "grove"
    folder.mkdir()
    (folder / "mossback.webp").write_bytes(b"OLD-PORTRAIT")
    result = dragon_art_html("dragon_grove_1", "Grove", 90)
    assert base64.b64encode(b"OLD-PORTRAIT").decode("ascii") in result


def test_codex_uses_full_portrait_instead_of_card_crop():
    """The selected dragon detail view requests a full illustration."""
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "app.py"
    ).read_text(encoding="utf-8")
    assert "dragon_art_html(selected, family, 180, portrait=True)" in (
        source
    ) or "dragon_art_html(selected, family, 240, portrait=True)" in (
        source
    )


@pytest.mark.parametrize(
    ("card_id", "element"),
    [("starter_flame", "Flame"), ("starter_tide", "Tide")],
)
def test_starters_use_artwork_when_available(
    tmp_path, monkeypatch, card_id, element
):
    """Starter portraits render without entering the collectible Codex."""
    monkeypatch.setattr(art_assets, "ASSET_ROOT", tmp_path)
    relative = art_assets.DRAGON_ART[card_id]
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"STARTER-ART")
    html = dragon_art_html(card_id, element, 112)
    encoded = base64.b64encode(b"STARTER-ART").decode("ascii")
    assert encoded in html
    assert "<img " in html


def test_missing_starter_image_falls_back_to_svg(tmp_path, monkeypatch):
    """The game still starts correctly without an artwork ZIP."""
    monkeypatch.setattr(art_assets, "ASSET_ROOT", tmp_path)
    assert dragon_art_html("starter_flame", "Flame", 112) == (
        dragon_svg("Flame", 112, 0)
    )


def test_every_registered_artwork_has_a_thumbnail_path():
    """Full portraits and thumbnails use consistent relative paths."""
    for card_id, portrait in art_assets.DRAGON_ART.items():
        assert portrait.endswith(".webp")
        assert art_assets.DRAGON_THUMBNAILS[card_id] == (
            portrait.replace(".webp", "-thumb.webp")
        )


def test_existing_dragon_abilities_unchanged():
    """Adding portraits cannot modify dragon mechanics or statistics."""
    from dragon_realms.engine import make_catalog

    catalog = make_catalog()
    assert catalog["starter_flame"].power == 1
    assert catalog["starter_tide"].power == 1
    assert catalog["dragon_storm_8"].power == 3
    assert catalog["dragon_stone_1"].effect == "stone_guard"


def test_new_batch_names_match_canonical_dragon_catalog():
    """Artwork filenames correspond to actual named dragon cards."""
    from dragon_realms.engine import make_catalog

    catalog = make_catalog()
    new_names = {
        "dragon_flame_1": "Cinderwing",
        "dragon_tide_1": "Riptalon",
        "dragon_tide_2": "Mistfin",
        "dragon_grove_2": "Thornroot",
        "dragon_grove_3": "Fernwhisper",
        "dragon_storm_1": "Sparkcrest",
        "dragon_stone_2": "Flintjaw",
        "dragon_shadow_2": "Nightwhisper",
    }
    for card_id, name in new_names.items():
        assert catalog[card_id].name == name
        assert art_assets.DRAGON_ART[card_id].endswith(
            f"/{name.lower()}.webp"
        )


def test_new_batch_all_elements_have_illustrated_options():
    """Every elemental family has at least one collectible illustration."""
    from dragon_realms.engine import ELEMENTS, make_catalog

    catalog = make_catalog()
    for element in ELEMENTS:
        matches = [
            card_id
            for card_id in art_assets.DRAGON_ART
            if catalog[card_id].element == element
            and card_id.startswith("dragon_")
        ]
        assert matches, f"{element} has no collectible artwork"


def test_v022_artwork_matches_eight_canonical_names():
    """The next art batch names match the engine's dragon definitions."""
    from dragon_realms.engine import make_catalog

    catalog = make_catalog()
    names = {
        "dragon_flame_2": "Ashmaw",
        "dragon_flame_4": "Emberclaw",
        "dragon_tide_3": "Coralcrest",
        "dragon_tide_6": "Pearlscale",
        "dragon_grove_4": "Briarwing",
        "dragon_storm_2": "Cloudbreaker",
        "dragon_stone_3": "Boulderspine",
        "dragon_shadow_3": "Umbraclaw",
    }
    for card_id, name in names.items():
        assert catalog[card_id].name == name
        assert art_assets.DRAGON_ART[card_id].endswith(
            f"/{name.lower()}.webp"
        )


def test_v023_artwork_identifies_eight_distinct_dragons():
    """Every new illustration matches a canonical dragon identity."""
    from dragon_realms.engine import make_catalog

    catalog = make_catalog()
    names = {
        "dragon_flame_3": "Pyrelash",
        "dragon_flame_5": "Scorchscale",
        "dragon_tide_4": "Deepglide",
        "dragon_grove_5": "Oakheart",
        "dragon_storm_3": "Thundermaw",
        "dragon_storm_4": "Galestrike",
        "dragon_stone_4": "Slatehorn",
        "dragon_shadow_4": "Gloomwing",
    }
    for card_id, name in names.items():
        assert catalog[card_id].name == name
        assert art_assets.DRAGON_ART[card_id].endswith(
            f"/{name.lower()}.webp"
        )


def test_v023_artwork_has_no_duplicate_paths():
    """New portraits do not overwrite any previous dragon identity."""
    portrait_paths = list(art_assets.DRAGON_ART.values())
    thumbnail_paths = list(art_assets.DRAGON_THUMBNAILS.values())
    assert len(portrait_paths) == len(set(portrait_paths))
    assert len(thumbnail_paths) == len(set(thumbnail_paths))


def test_v024_artwork_matches_canonical_card_names():
    """All eight new portraits belong to the correct game dragons."""
    from dragon_realms.engine import make_catalog

    catalog = make_catalog()
    names = {
        "dragon_flame_6": "Blazehorn",
        "dragon_flame_7": "Kindlefang",
        "dragon_tide_5": "Wavecaller",
        "dragon_tide_7": "Foamwing",
        "dragon_grove_6": "Bloomtail",
        "dragon_storm_5": "Skyshiver",
        "dragon_stone_5": "Cragheart",
        "dragon_shadow_5": "Echofang",
    }
    for card_id, name in names.items():
        assert catalog[card_id].name == name
        assert art_assets.DRAGON_ART[card_id].endswith(
            f"/{name.lower()}.webp"
        )

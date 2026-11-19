"""Tests for the optional v0.19 illustrated dragon art assets."""

import base64
from pathlib import Path

import pytest

from dragon_realms import art_assets
from dragon_realms.art_assets import dragon_art_html, dragon_art_path
from dragon_realms.artwork import dragon_svg


def test_registry_contains_seven_illustrated_dragons():
    """The artwork registry uses stable IDs for the seven portraits."""
    assert art_assets.DRAGON_ART == {
        "starter_flame": "flame/starter_flame.webp",
        "starter_tide": "tide/starter_tide.webp",
        "dragon_flame_8": "flame/infernos.webp",
        "dragon_grove_1": "grove/mossback.webp",
        "dragon_stone_1": "stone/granitehide.webp",
        "dragon_storm_8": "storm/stormspire.webp",
        "dragon_shadow_1": "shadow/duskveil.webp",
    }
    assert len(art_assets.DRAGON_THUMBNAILS) == 7


def test_missing_art_uses_original_svg():
    """Artwork is optional, including on other dragon cards."""
    assert dragon_art_html("dragon_flame_5", "Flame", 80) == (
        dragon_svg("Flame", 80, 5)
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

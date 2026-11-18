"""Tests for the optional v0.19 illustrated dragon art assets."""

import base64
from pathlib import Path

import pytest

from dragon_realms import art_assets
from dragon_realms.art_assets import dragon_art_html, dragon_art_path
from dragon_realms.artwork import dragon_svg


def test_registry_contains_three_showcase_dragons():
    """The initial illustrations use existing, stable card IDs."""
    assert art_assets.DRAGON_ART == {
        "dragon_stone_1": "stone/granitehide.webp",
        "dragon_storm_8": "storm/stormspire.webp",
        "dragon_grove_1": "grove/mossback.webp",
    }


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

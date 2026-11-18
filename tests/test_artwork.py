"""Tests for the original Dragon Realms elemental artwork."""

from xml.etree import ElementTree

import pytest

from dragon_realms.artwork import (
    ELEMENT_SIGILS,
    PALETTES,
    dragon_svg,
)
from dragon_realms.engine import ELEMENTS


@pytest.mark.parametrize("element", ELEMENTS)
def test_element_art_is_valid_accessible_svg(element):
    """Each element provides valid, self-contained accessible artwork."""
    artwork = dragon_svg(element)
    root = ElementTree.fromstring(artwork)
    assert root.tag.endswith("svg")
    assert root.attrib["role"] == "img"
    assert element in root.attrib["aria-label"]
    assert root.attrib["viewBox"] == "0 0 120 92"
    assert len(list(root.iter())) >= 12
    assert "url(#body)" not in artwork


def test_artwork_has_six_distinct_elemental_styles():
    """Different dragon families have separate palettes and sigils."""
    assert set(PALETTES) == set(ELEMENTS)
    assert set(ELEMENT_SIGILS) == set(ELEMENTS)
    assert len(set(PALETTES.values())) == len(ELEMENTS)
    assert len({dragon_svg(name) for name in ELEMENTS}) == 6


def test_artwork_scale_is_configurable():
    """Compact and large renderings preserve the artwork geometry."""
    small = ElementTree.fromstring(dragon_svg("Tide", 48))
    large = ElementTree.fromstring(dragon_svg("Tide", 144))
    assert small.attrib["width"] == "48"
    assert large.attrib["width"] == "144"
    assert small.attrib["viewBox"] == large.attrib["viewBox"]


@pytest.mark.parametrize("bad_size", [0, 23, 513, True, 56.5])
def test_reject_invalid_artwork_sizes(bad_size):
    """Invalid dimensions are rejected rather than silently coerced."""
    with pytest.raises(ValueError):
        dragon_svg("Grove", bad_size)


def test_reject_unknown_element():
    """Only game-defined dragon elements can be rendered."""
    with pytest.raises(ValueError, match="Unknown dragon element"):
        dragon_svg("Sun")


def test_svg_gradients_are_referenced_by_their_own_cards():
    """Every dragon references the gradient defined in its SVG."""
    for name in ELEMENTS:
        svg = dragon_svg(name)
        gradient = f"dragon-body-{name.lower()}"
        assert f'id="{gradient}"' in svg
        assert f"url(#{gradient})" in svg

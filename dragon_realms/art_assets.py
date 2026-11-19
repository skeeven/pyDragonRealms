"""Safe, optional illustrated dragon portraits with SVG fallback.

WebP assets live in assets/dragons/ and are identified by stable card IDs.
No network fetches, arbitrary user paths, or new dependencies are needed.
"""

from __future__ import annotations

import base64
from functools import lru_cache
from html import escape
from pathlib import Path

from .artwork import dragon_svg
from .dragon_identity import dragon_variant

ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets" / "dragons"

DRAGON_ART = {
    "starter_flame": "flame/starter_flame.webp",
    "starter_tide": "tide/starter_tide.webp",
    "dragon_flame_8": "flame/infernos.webp",
    "dragon_grove_1": "grove/mossback.webp",
    "dragon_stone_1": "stone/granitehide.webp",
    "dragon_storm_8": "storm/stormspire.webp",
    "dragon_shadow_1": "shadow/duskveil.webp",
    "dragon_flame_1": "flame/cinderwing.webp",
    "dragon_tide_1": "tide/riptalon.webp",
    "dragon_tide_2": "tide/mistfin.webp",
    "dragon_grove_2": "grove/thornroot.webp",
    "dragon_grove_3": "grove/fernwhisper.webp",
    "dragon_storm_1": "storm/sparkcrest.webp",
    "dragon_stone_2": "stone/flintjaw.webp",
    "dragon_shadow_2": "shadow/nightwhisper.webp",
    "dragon_flame_2": "flame/ashmaw.webp",
    "dragon_flame_4": "flame/emberclaw.webp",
    "dragon_tide_3": "tide/coralcrest.webp",
    "dragon_tide_6": "tide/pearlscale.webp",
    "dragon_grove_4": "grove/briarwing.webp",
    "dragon_storm_2": "storm/cloudbreaker.webp",
    "dragon_stone_3": "stone/boulderspine.webp",
    "dragon_shadow_3": "shadow/umbraclaw.webp",
    "dragon_flame_3": "flame/pyrelash.webp",
    "dragon_flame_5": "flame/scorchscale.webp",
    "dragon_tide_4": "tide/deepglide.webp",
    "dragon_grove_5": "grove/oakheart.webp",
    "dragon_storm_3": "storm/thundermaw.webp",
    "dragon_storm_4": "storm/galestrike.webp",
    "dragon_stone_4": "stone/slatehorn.webp",
    "dragon_shadow_4": "shadow/gloomwing.webp",
    "dragon_flame_6": "flame/blazehorn.webp",
    "dragon_flame_7": "flame/kindlefang.webp",
    "dragon_tide_5": "tide/wavecaller.webp",
    "dragon_tide_7": "tide/foamwing.webp",
    "dragon_grove_6": "grove/bloomtail.webp",
    "dragon_storm_5": "storm/skyshiver.webp",
    "dragon_stone_5": "stone/cragheart.webp",
    "dragon_shadow_5": "shadow/echofang.webp",
    "dragon_tide_8": "tide/abyssal.webp",
    "dragon_grove_7": "grove/verdant.webp",
    "dragon_grove_8": "grove/wildbloom.webp",
    "dragon_storm_6": "storm/voltwing.webp",
    "dragon_storm_7": "storm/tempestral.webp",
    "dragon_stone_6": "stone/ironridge.webp",
    "dragon_shadow_6": "shadow/moonshade.webp",
    "dragon_shadow_7": "shadow/voidscale.webp",
    "dragon_stone_7": "stone/obsidian.webp",
    "dragon_stone_8": "stone/mountainborn.webp",
    "dragon_shadow_8": "shadow/nocturne.webp",
}

DRAGON_THUMBNAILS = {
    card_id: path.replace(".webp", "-thumb.webp")
    for card_id, path in DRAGON_ART.items()
}

MAX_ART_BYTES = 2_000_000


def dragon_art_path(card_id: str, portrait: bool = False) -> Path | None:
    """Return a validated local asset for a known collectible."""
    relative = (
        DRAGON_ART.get(card_id) if portrait
        else DRAGON_THUMBNAILS.get(card_id)
    )
    if relative is None:
        return None
    path = ASSET_ROOT / relative
    if not path.is_file() or path.stat().st_size > MAX_ART_BYTES:
        return None
    return path


@lru_cache(maxsize=64)
def _cached_image(path: str, modified_ns: int) -> str:
    """Encode a trusted local portrait for compact inline cards."""
    del modified_ns
    encoded = base64.b64encode(Path(path).read_bytes()).decode("ascii")
    return f"data:image/webp;base64,{encoded}"


def dragon_art_html(
    card_id: str,
    element: str,
    size: int = 112,
    variant: int | None = None,
    portrait: bool = False,
) -> str:
    """Render illustrated WebP artwork or a self-contained SVG fallback."""
    if not isinstance(size, int) or isinstance(size, bool):
        raise ValueError("Image size must be an integer")
    if not 24 <= size <= 512:
        raise ValueError("Image size must be between 24 and 512")
    if variant is None:
        variant = dragon_variant(card_id)
    path = dragon_art_path(card_id, portrait=portrait)
    if path is None and not portrait:
        path = dragon_art_path(card_id, portrait=True)
    if path is None:
        return dragon_svg(element, size, variant)
    src = _cached_image(str(path), path.stat().st_mtime_ns)
    title = escape(f"{element} dragon illustration", quote=True)
    if portrait:
        return (
            f'<img src="{src}" alt="{title}" loading="lazy" '
            f'width="{size}" '
            'style="display:block;width:100%;height:auto;'
            'object-fit:contain;" />'
        )
    return (
        f'<img src="{src}" alt="{title}" loading="lazy" '
        f'width="{size}" height="{size}" '
        'style="display:block;object-fit:cover;aspect-ratio:1/1;" />'
    )

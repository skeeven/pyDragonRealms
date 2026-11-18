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
    "dragon_stone_1": "stone/granitehide.webp",
    "dragon_storm_8": "storm/stormspire.webp",
    "dragon_grove_1": "grove/mossback.webp",
}

MAX_ART_BYTES = 2_000_000


def dragon_art_path(card_id: str) -> Path | None:
    """Return a validated local asset for a known collectible."""
    relative = DRAGON_ART.get(card_id)
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
    path = dragon_art_path(card_id)
    if path is None:
        return dragon_svg(element, size, variant)
    src = _cached_image(str(path), path.stat().st_mtime_ns)
    title = escape(f"{element} dragon illustration", quote=True)
    height = size * 3 // 2 if portrait else size
    ratio = "2/3" if portrait else "1/1"
    return (
        f'<img src="{src}" alt="{title}" loading="lazy" '
        f'width="{size}" height="{height}" '
        f'style="display:block;object-fit:cover;aspect-ratio:{ratio};" />'
    )

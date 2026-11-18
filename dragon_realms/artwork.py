"""Original, self-contained SVG artwork for six elemental dragon families."""

from __future__ import annotations

from html import escape

PALETTES = {
    "Flame": ("#fa7241", "#8b2930", "#ffcc75", "#2b101d"),
    "Tide": ("#54c9e8", "#256baf", "#b3f5fc", "#0d2946"),
    "Grove": ("#8bcf70", "#3e805e", "#dcf5a2", "#162c2b"),
    "Storm": ("#d3b7ff", "#7458c9", "#f8e99e", "#20244d"),
    "Stone": ("#b6b8c2", "#65788a", "#f3dfb7", "#29313d"),
    "Shadow": ("#bf9adf", "#644889", "#f1b9ea", "#20142f"),
}

# Decorative silhouettes appear behind the same readable dragon shape.
ELEMENT_SIGILS = {
    "Flame": (
        '<path d="M38 83 Q9 51 42 15 Q39 46 57 53'
        ' Q67 34 65 15 Q101 48 85 80" '
        'fill="none" stroke="#ffad54" stroke-width="4" '
        'stroke-linecap="round" opacity=".75"/>'
    ),
    "Tide": (
        '<path d="M10 67 Q32 44 54 67 T98 67 '
        'M9 80 Q35 57 61 80 T104 80" '
        'fill="none" stroke="#8deaff" stroke-width="4" '
        'stroke-linecap="round" opacity=".75"/>'
    ),
    "Grove": (
        '<path d="M20 77 Q9 43 33 20 Q57 41 34 65 '
        'M84 71 Q103 43 83 20 Q59 37 73 61" '
        'fill="none" stroke="#d5f8a3" stroke-width="4" '
        'stroke-linecap="round" opacity=".8"/>'
    ),
    "Storm": (
        '<path d="M20 20 L38 37 L28 48 L48 62 '
        'M87 10 L65 36 L83 41 L62 65" '
        'fill="none" stroke="#f4dc81" stroke-width="5" '
        'stroke-linejoin="round" opacity=".9"/>'
    ),
    "Stone": (
        '<path d="M20 25 L40 10 L61 24 L52 48 L28 51 Z '
        'M82 50 L100 38 L111 57 L91 72 L75 65 Z" '
        'fill="none" stroke="#d5d6dc" stroke-width="3" '
        'stroke-linejoin="round" opacity=".7"/>'
    ),
    "Shadow": (
        '<path d="M65 12 A41 41 0 1 0 93 77 '
        'A29 29 0 1 1 65 12 Z" '
        'fill="#d2adee" opacity=".38"/>'
        '<circle cx="26" cy="22" r="2" fill="#ffe4ff"/>'
        '<circle cx="95" cy="29" r="2" fill="#ffe4ff"/>'
    ),
}


def dragon_svg(element: str, size: int = 112) -> str:
    """Render original lightweight dragon artwork without external assets."""
    if element not in PALETTES:
        raise ValueError(f"Unknown dragon element: {element}")
    if not isinstance(size, int) or not 24 <= size <= 512:
        raise ValueError("Artwork size must be between 24 and 512 pixels")
    primary, secondary, highlight, background = PALETTES[element]
    title = escape(f"{element} dragon illustration", quote=True)
    sigil = ELEMENT_SIGILS[element]
    gradient_id = f"dragon-body-{element.lower()}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 120 92" width="{size}" height="{size * 92 // 120}" '
        f'role="img" aria-label="{title}" focusable="false">'
        '<defs>'
        f'<linearGradient id="{gradient_id}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop stop-color="{primary}"/>'
        f'<stop offset="1" stop-color="{secondary}"/>'
        '</linearGradient>'
        '</defs>'
        f'<rect x="1" y="1" width="118" height="90" rx="16" '
        f'fill="{background}" opacity=".92"/>'
        '<circle cx="59" cy="45" r="35" fill="none" '
        f'stroke="{highlight}" opacity=".22" stroke-width="1.5"/>'
        f'{sigil}'
        '<path d="M43 64 Q10 90 14 60 Q25 74 43 57" '
        f'fill="url(#{gradient_id})" opacity=".9"/>'
        '<path d="M51 52 Q26 7 10 22 Q23 32 29 55 '
        f'L18 49 Q30 72 52 66 Z" fill="url(#{gradient_id})" '
        f'stroke="{highlight}" stroke-width="1.3" opacity=".9"/>'
        '<path d="M67 51 Q85 8 109 25 Q90 33 87 57 '
        f'L103 46 Q96 72 67 67 Z" fill="url(#{gradient_id})" '
        f'stroke="{highlight}" stroke-width="1.3" opacity=".86"/>'
        '<path d="M49 76 Q42 61 45 47 Q48 35 61 34 '
        'L69 27 L75 37 L88 38 L96 45 L90 51 '
        'L74 52 Q75 63 83 72 Q64 83 49 76 Z" '
        f'fill="url(#{gradient_id})" '
        f'stroke="{highlight}" stroke-width="1.5"/>'
        '<path d="M66 35 L64 20 L72 30 L79 19 L78 38" '
        f'fill="url(#{gradient_id})" '
        f'stroke="{highlight}" stroke-width="1.4"/>'
        f'<path d="M81 42 L88 43" stroke="{highlight}" '
        'stroke-width="2.7" stroke-linecap="round"/>'
        '<path d="M52 70 Q64 74 73 69" fill="none" '
        f'stroke="{highlight}" stroke-width="2" opacity=".6"/>'
        '</svg>'
    )

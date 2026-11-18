"""Distinct names and lore for Dragon Realms collectible dragons.

Card IDs remain stable across versions; these are display-only identities.
"""

from __future__ import annotations

DRAGON_NAMES = {
    "Flame": (
        "Cinderwing", "Ashmaw", "Pyrelash", "Emberclaw",
        "Scorchscale", "Blazehorn", "Kindlefang", "Infernos",
    ),
    "Tide": (
        "Riptalon", "Mistfin", "Coralcrest", "Deepglide",
        "Wavecaller", "Pearlscale", "Foamwing", "Abyssal",
    ),
    "Grove": (
        "Mossback", "Thornroot", "Fernwhisper", "Briarwing",
        "Oakheart", "Bloomtail", "Verdant", "Wildbloom",
    ),
    "Storm": (
        "Sparkcrest", "Cloudbreaker", "Thundermaw", "Galestrike",
        "Skyshiver", "Voltwing", "Tempestral", "Stormspire",
    ),
    "Stone": (
        "Granitehide", "Flintjaw", "Boulderspine", "Slatehorn",
        "Cragheart", "Ironridge", "Obsidian", "Mountainborn",
    ),
    "Shadow": (
        "Duskveil", "Nightwhisper", "Umbraclaw", "Gloomwing",
        "Echofang", "Moonshade", "Voidscale", "Nocturne",
    ),
}

ELEMENT_LORE = {
    "Flame": (
        "Guardians of the first forge",
        "carry embers from the sleeping mountain.",
    ),
    "Tide": (
        "Keepers of the hidden current",
        "trace the moon through ancient seas.",
    ),
    "Grove": (
        "Protectors of the waking forest",
        "listen to the roots beneath the realm.",
    ),
    "Storm": (
        "Riders of the thunder frontier",
        "chase the lightning beyond the clouds.",
    ),
    "Stone": (
        "Sentinels of the old peaks",
        "remember promises carved in granite.",
    ),
    "Shadow": (
        "Watchers of the twilight paths",
        "guard secrets forgotten by daylight.",
    ),
}

DRAGON_TITLES = (
    "the Wanderer",
    "the Watchful",
    "the Keeper",
    "the Bold",
    "the Ancient",
    "the Swift",
    "the Boundless",
    "the Eternal",
)


def dragon_variant(card_id: str) -> int:
    """Return a collectible's visual variant; starters use zero."""
    if card_id.startswith("starter_"):
        return 0
    parts = card_id.split("_")
    if (
        len(parts) != 3
        or parts[0] != "dragon"
        or parts[1].title() not in DRAGON_NAMES
        or not parts[2].isdigit()
    ):
        raise ValueError(f"Unknown dragon card ID: {card_id}")
    number = int(parts[2])
    if not 1 <= number <= 8:
        raise ValueError(f"Unknown dragon variant: {card_id}")
    return number


def dragon_name(element: str, index: int) -> str:
    """Return the permanent name of one numbered dragon definition."""
    return DRAGON_NAMES[element][index - 1]


def dragon_lore(card_id: str) -> str:
    """Describe a collectible without changing its rules or stats."""
    variant = dragon_variant(card_id)
    if variant == 0:
        return "A young dragon beginning its journey with its Warden."
    element = card_id.split("_")[1].title()
    opening, ending = ELEMENT_LORE[element]
    name = DRAGON_NAMES[element][variant - 1]
    title = DRAGON_TITLES[variant - 1]
    return f"{name}, {title}. {opening}; they {ending}"

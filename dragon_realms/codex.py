"""Dragon Codex discovery views derived from authoritative game history."""

from __future__ import annotations

from .dragon_identity import dragon_lore, dragon_variant
from .engine import ELEMENTS, Game


def discovered_dragons(game: Game, pid: str) -> set[str]:
    """Find dragons the Warden has ever acquired in this match.

    Legacy events without card IDs are ignored. Dragons currently owned
    still count, so old save files retain their visible collection.
    """
    player = game.players[pid]
    found = {
        dragon.card_id
        for dragon in player.deployed + player.reserve
        if dragon.card_id.startswith("dragon_")
    }
    for event in game.events:
        if event.get("player") != pid:
            continue
        if event.get("event") in ("auction_won", "deployed"):
            card_id = event.get("card_id")
        elif (event.get("event") == "action"
              and event.get("action") in ("recruit", "meditate")):
            card_id = event.get("acquired_dragon_id")
        else:
            continue
        if isinstance(card_id, str) and card_id in game.cards:
            if game.cards[card_id].kind == "dragon":
                if not card_id.startswith("starter_"):
                    found.add(card_id)
    return found


def codex_entries(game: Game, pid: str,
                  element: str | None = None) -> list[dict]:
    """Return catalog entries with the Warden's discovery status."""
    if pid not in game.players:
        raise ValueError("Unknown Warden")
    if element is not None and element not in ELEMENTS:
        raise ValueError("Unknown element")
    owned = {
        item.card_id
        for item in (
            game.players[pid].deployed + game.players[pid].reserve
        )
    }
    discovered = discovered_dragons(game, pid)
    entries = []
    for family in ELEMENTS:
        if element is not None and family != element:
            continue
        for variant in range(1, 9):
            card_id = f"dragon_{family.lower()}_{variant}"
            card = game.cards[card_id]
            known = card_id in discovered
            entries.append({
                "card_id": card_id,
                "variant": dragon_variant(card_id),
                "element": family,
                "status": (
                    "Owned" if card_id in owned
                    else "Discovered" if known else "Unknown"
                ),
                "name": card.name if known else "Undiscovered",
                "lore": dragon_lore(card_id) if known else "",
                "power": card.power if known else None,
                "prestige": card.prestige if known else None,
                "effect": card.effect if known else "",
            })
    return entries


def codex_summary(game: Game, pid: str) -> dict[str, int]:
    """Count discovered and currently held distinct collectible dragons."""
    entries = codex_entries(game, pid)
    return {
        "discovered": sum(
            item["status"] != "Unknown" for item in entries
        ),
        "owned": sum(item["status"] == "Owned" for item in entries),
        "total": len(entries),
    }


def family_progress(game: Game, pid: str) -> list[dict]:
    """Summarize discovery progress for each elemental family."""
    result = []
    for element in ELEMENTS:
        entries = codex_entries(game, pid, element)
        discovered = sum(
            item["status"] != "Unknown" for item in entries
        )
        result.append({
            "element": element,
            "discovered": discovered,
            "owned": sum(
                item["status"] == "Owned" for item in entries
            ),
            "total": len(entries),
        })
    return result

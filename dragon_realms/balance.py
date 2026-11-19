"""Read-only catalog and simulation balance audit for Dragon Realms.

Run: python3 -m dragon_realms.balance --games 500 --seed 0
"""

from __future__ import annotations

import argparse
import json
from collections import Counter

from .engine import CAP, DRAGON_ABILITIES, RESOURCES, make_catalog
from .simulate import simulate


def catalog_audit() -> dict:
    """Report rules coverage and detect broken content definitions."""
    catalog = make_catalog()
    dragons = [
        card for card in catalog.values() if card.kind == "dragon"
    ]
    elements = Counter(card.element for card in dragons)
    effects = Counter(card.effect or "(none)" for card in dragons)
    relics = [
        card for card in catalog.values() if card.kind == "relic"
    ]
    buildings = [
        card for card in catalog.values() if card.kind == "building"
    ]
    quests = [
        card for card in catalog.values() if card.kind == "quest"
    ]
    invalid = []
    for card in catalog.values():
        if any(
            kind not in RESOURCES
            or type(amount) is not int
            or amount < 0
            or amount > CAP
            for kind, amount in card.cost.items()
        ):
            invalid.append(f"{card.id}: invalid cost")
        if card.kind == "dragon":
            if not card.element or card.power < 1:
                invalid.append(f"{card.id}: invalid dragon stats")
            if card.effect and card.effect not in DRAGON_ABILITIES:
                invalid.append(f"{card.id}: unknown dragon ability")
        if card.kind == "quest":
            if card.reward.get("prestige", 0) < 1:
                invalid.append(f"{card.id}: no prestige reward")
            if card.requirement.get("power", 0) < 1:
                invalid.append(f"{card.id}: missing power requirement")
    return {
        "card_count": len(catalog),
        "dragon_count": len(dragons),
        "elements": dict(sorted(elements.items())),
        "dragon_abilities": dict(sorted(effects.items())),
        "building_count": len(buildings),
        "relic_count": len(relics),
        "relic_effects": dict(sorted(Counter(
            card.effect or "(none)" for card in relics
        ).items())),
        "quest_count": len(quests),
        "issues": invalid,
    }


def balance_report(games: int = 100, seed: int = 0) -> dict:
    """Combine a static ability audit with a reproducible match sample."""
    return {
        "catalog": catalog_audit(),
        "simulation": simulate(
            games=games, players=4, seed=seed, rounds=8
        ),
    }


def main() -> None:
    """Print a machine-readable audit for design comparisons."""
    parser = argparse.ArgumentParser(description="Dragon Realms balance audit")
    parser.add_argument("--games", type=int, default=100)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    print(json.dumps(balance_report(args.games, args.seed), indent=2))


if __name__ == "__main__":
    main()

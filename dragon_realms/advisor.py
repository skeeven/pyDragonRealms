"""Read-only strategic guidance for human Dragon Realms players."""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Any

from .bots import quest_options
from .engine import Game


BOND_COSTS = (
    {"ember": 2},
    {"ember": 2, "aether": 1},
    {"ember": 3, "aether": 2},
)


def affordable(resources: dict[str, int],
               cost: dict[str, int]) -> bool:
    """Return whether the player can pay for a card or action."""
    return all(resources.get(key, 0) >= amount
               for key, amount in cost.items())


def team_power(game: Game, dragons) -> int:
    """Calculate quest power with the same modifiers as the engine."""
    return sum(
        game.cards[d.card_id].power + d.bond
        + (2 if game.cards[d.card_id].effect == "flame_focus"
           else int(game.cards[d.card_id].effect == "storm_boost"))
        for d in dragons
    )


def effective_quest_power(game: Game, pid: str, team) -> int:
    """Calculate printed and passive power for a proposed quest team."""
    player = game.players[pid]
    power = team_power(game, team)
    if any(
        game.cards[item.card_id].effect == "quest_power"
        for item in player.buildings
    ):
        power += 1
    if (
        len({game.cards[item.card_id].element for item in team}) >= 3
        and any(
            game.cards[item.card_id].effect == "prism"
            for item in player.relics
        )
    ):
        power += 1
    return power


def quest_previews(game: Game, pid: str) -> list[dict[str, Any]]:
    """Describe every public quest without mutating the match.

    Among feasible teams, prefer fewer dragons; then save stronger
    dragons for a possible second quest this round.
    """
    player = game.players[pid]
    options = defaultdict(list)
    for quest, dragons, prestige in quest_options(game, pid):
        options[quest.uid].append((dragons, prestige))

    ready = [dragon for dragon in player.deployed
             if not dragon.exhausted]
    bonus = int(any(game.cards[b.card_id].effect == "quest_power"
                    for b in player.buildings))
    prism = any(
        game.cards[r.card_id].effect == "prism"
        for r in player.relics
    )
    max_power = max(
        (
            team_power(game, team) + bonus
            + int(prism and len({
                game.cards[d.card_id].element for d in team
            }) >= 3)
            for size in range(1, min(3, len(ready)) + 1)
            for team in combinations(ready, size)
        ),
        default=0,
    )
    previews = []

    for item in game.quests:
        card = game.cards[item.card_id]
        requirement = card.requirement
        teams = options.get(item.uid, [])
        chosen = None
        prestige = card.reward.get("prestige", 0)
        if teams:
            chosen, prestige = min(
                teams,
                key=lambda option: (
                    len(option[0]),
                    team_power(game, option[0]),
                    tuple(dragon.uid for dragon in option[0]),
                ),
            )
        reasons = []
        if not chosen:
            required_power = requirement.get("power", 0)
            if max_power < required_power:
                reasons.append(
                    f"Need {required_power} power; your strongest "
                    f"three ready dragons provide at most {max_power}."
                )
            needed_element = requirement.get("element")
            if needed_element and not any(
                game.cards[d.card_id].element == needed_element
                for d in ready
            ):
                reasons.append(
                    f"Need a ready {needed_element} dragon."
                )
            distinct = requirement.get("distinct", 0)
            available_elements = {
                game.cards[d.card_id].element for d in ready
            }
            if len(available_elements) < distinct:
                reasons.append(
                    f"Need {distinct} different elements; "
                    f"you have {len(available_elements)} ready."
                )
            if not reasons:
                reasons.append(
                    "No combination of up to three ready dragons "
                    "meets all requirements together."
                )

        reward = dict(card.reward)
        if chosen:
            for dragon in chosen:
                resource = {
                    "tide_bounty": "crystal",
                    "grove_bounty": "aether",
                }.get(game.cards[dragon.card_id].effect)
                if resource:
                    reward[resource] = reward.get(resource, 0) + 1

        previews.append({
            "uid": item.uid,
            "name": card.name,
            "requirement": dict(requirement),
            "reward": reward,
            "prestige": prestige,
            "team_power": (
                effective_quest_power(game, pid, chosen)
                if chosen else 0
            ),
            "power_surplus": (
                effective_quest_power(game, pid, chosen)
                - requirement.get("power", 0)
                if chosen else None
            ),
            "ready_after": (
                sum(dragon not in chosen for dragon in ready)
                if chosen else len(ready)
            ),
            "ready": chosen is not None,
            "dragon_uids": (
                [dragon.uid for dragon in chosen] if chosen else []
            ),
            "dragon_names": (
                [game.cards[dragon.card_id].name for dragon in chosen]
                if chosen else []
            ),
            "reasons": reasons,
        })
    return previews


def recommendation(game: Game, pid: str) -> dict[str, str]:
    """Suggest a useful move with a concrete, non-optimality claim."""
    player = game.players[pid]
    previews = [
        quest for quest in quest_previews(game, pid)
        if quest["ready"]
    ]
    if previews:
        best = max(
            previews,
            key=lambda quest: (
                quest["prestige"],
                -len(quest["dragon_uids"]),
            ),
        )
        return {
            "kind": "quest",
            "title": f"Complete {best['name']}",
            "reason": (
                f"Earn {best['prestige']} prestige now using "
                f"{len(best['dragon_uids'])} dragon(s). "
                "They rest until the next round, so check "
                "whether another quest needs them first."
            ),
        }

    buildings = [
        game.cards[item.card_id]
        for item in game.blueprints
        if len(player.buildings) < 3
        and affordable(
            player.resources, game.cards[item.card_id].cost
        )
    ]
    if buildings:
        best = max(buildings, key=lambda card: card.prestige)
        return {
            "kind": "build",
            "title": f"Build {best.name}",
            "reason": (
                f"Adds {best.prestige} base prestige immediately. "
                "Some buildings also provide lasting effects."
            ),
        }

    if game.round == game.max_rounds:
        return {
            "kind": "final",
            "title": "Seek immediate prestige",
            "reason": (
                "This is the final round. Unspent resources "
                "do not count toward your final score."
            ),
        }

    candidates = [
        dragon for dragon in player.deployed
        if dragon.bond < 3 and affordable(
            player.resources, BOND_COSTS[dragon.bond]
        )
    ]
    if candidates:
        return {
            "kind": "bond",
            "title": "Strengthen a dragon",
            "reason": (
                "Bonding adds quest power. Reaching bond level 2 "
                "also awards 1 prestige, and level 3 awards "
                "3 total bond prestige."
            ),
        }
    return {
        "kind": "channel",
        "title": "Gather resources",
        "reason": (
            "Channel two resources now to prepare for future "
            "bids, construction, or dragon bonds."
        ),
    }


def chapter(game: Game) -> str:
    """Provide a short game-plan hint appropriate to the round."""
    progress = (game.round - 1) / game.max_rounds
    if progress < 0.34:
        return (
            "Early game · Acquire and deploy strong, varied dragons. "
            "Resources and persistent buildings can pay off later."
        )
    if progress < 0.7:
        return (
            "Midgame · Complete quests with your ready dragons "
            "and develop your strongest long-term combinations."
        )
    return (
        "Endgame · Prioritize prestige now. Only deployed dragons "
        "score, so avoid leaving strong cards in reserve."
    )

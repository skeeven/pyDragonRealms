"""Strategy heuristics for Dragon Realms simulations.

Bots use the same public Game methods as human players.
"""
from __future__ import annotations

from itertools import combinations

from .engine import Game, RuleError


def value(game: Game, item) -> float:
    card = game.cards[item.card_id]
    return card.prestige + 0.45 * card.power


def deploy_best(game: Game, pid: str) -> None:
    player = game.players[pid]
    if not player.reserve or player.swapped:
        return
    candidate = max(player.reserve, key=lambda d: value(game, d))
    if len(player.deployed) < 5:
        game.deploy(pid, candidate.uid)
        return
    weakest = min(player.deployed, key=lambda d: value(game, d))
    if not weakest.exhausted and value(game, candidate) > value(game, weakest):
        game.deploy(pid, candidate.uid, weakest.uid)


def quest_options(game: Game, pid: str):
    """Return feasible (quest, dragons, reward) tuples without changing state."""
    player = game.players[pid]
    ready = [d for d in player.deployed if not d.exhausted]
    power_bonus = int(any(game.cards[b.card_id].effect == "quest_power"
                          for b in player.buildings))
    prism = any(game.cards[r.card_id].effect == "prism"
                for r in player.relics)
    for quest in game.quests:
        card = game.cards[quest.card_id]
        req = card.requirement
        for size in range(1, min(3, len(ready)) + 1):
            for dragons in combinations(ready, size):
                elements = {game.cards[d.card_id].element for d in dragons}
                power = sum(game.cards[d.card_id].power + d.bond
                            for d in dragons) + power_bonus
                power += int(prism and len(elements) >= 3)
                if (power >= req.get("power", 0)
                        and (not req.get("element")
                             or req["element"] in elements)
                        and len(elements) >= req.get("distinct", 0)):
                    yield quest, dragons, card.reward.get("prestige", 0)


def choose_action(game: Game, pid: str, strategy: str) -> str:
    player = game.players[pid]
    options = list(quest_options(game, pid))
    if options:
        quest, dragons, _ = max(
            options, key=lambda x: (x[2], -len(x[1])))
        game.act(pid, "quest", uid=quest.uid,
                 dragons=[d.uid for d in dragons])
        return "quest"

    if strategy in ("balanced", "builder") and len(player.buildings) < 3:
        affordable = [b for b in game.blueprints
                      if all(player.resources.get(k, 0) >= v
                             for k, v in game.cards[b.card_id].cost.items())]
        if affordable:
            target = max(affordable, key=lambda b: value(game, b))
            game.act(pid, "build", uid=target.uid)
            return "build"

    if strategy in ("bonding", "balanced"):
        costs = ({"ember": 2}, {"ember": 2, "aether": 1},
                 {"ember": 3, "aether": 2})
        candidates = [d for d in player.deployed if d.bond < 3 and
                      all(player.resources.get(k, 0) >= v
                          for k, v in costs[d.bond].items())]
        if candidates:
            target = max(candidates, key=lambda d:
                         (d.bond, value(game, d)))
            game.act(pid, "bond", uid=target.uid)
            return "bond"

    if strategy == "collector" and len(player.reserve) < 7:
        if game.decks["dragon"]:
            card = game.cards[game.decks["dragon"][-1]]
            if all(player.resources.get(k, 0) >= v
                   for k, v in card.cost.items()):
                game.act(pid, "recruit")
                return "recruit"

    game.act(pid, "channel", gains={"ember": 1, "aether": 1})
    return "channel"


def score_breakdown(game: Game, pid: str) -> dict[str, int]:
    """Calculate additive scoring components matching Game.score."""
    player = game.players[pid]
    dragons = sum(game.cards[d.card_id].prestige
                  for d in player.deployed)
    bonds = sum((0, 0, 1, 3)[d.bond] for d in player.deployed)
    buildings = sum(game.cards[b.card_id].prestige
                    for b in player.buildings)
    buildings += sum(min(5, len(player.deployed))
                     for b in player.buildings
                     if game.cards[b.card_id].effect == "warden_hall")
    relics = sum(game.cards[r.card_id].prestige for r in player.relics)
    for relic in player.relics:
        if game.cards[relic.card_id].effect == "ember_crown":
            relics += min(4, 2 * sum(
                d.bond == 3 and game.cards[d.card_id].element == "Flame"
                for d in player.deployed))
    elements = [game.cards[d.card_id].element for d in player.deployed]
    nonstarter = [game.cards[d.card_id].element for d in player.deployed
                  if not d.card_id.startswith("starter_")]
    triples = any(nonstarter.count(element) >= 3
                  for element in set(nonstarter))
    diversity = len(set(elements))
    synergy = max(3 if triples else 0, 5 if diversity >= 4 else 0,
                  8 if diversity >= 5 else 0)
    result = {"quests": player.quest_prestige, "dragons": dragons,
              "bonds": bonds, "buildings": buildings,
              "relics": relics, "synergy": synergy}
    assert sum(result.values()) == game.score(pid)
    return result

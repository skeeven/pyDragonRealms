"""Strategy heuristics for Dragon Realms simulations.

Bots use the same public Game methods as human players.
"""
from __future__ import annotations

from itertools import combinations

from .engine import Game, RuleError


BOND_COSTS = (
    {"ember": 2},
    {"ember": 2, "aether": 1},
    {"ember": 3, "aether": 2},
)


def _affordable(resources: dict[str, int],
                cost: dict[str, int]) -> bool:
    """Check whether a player can afford a chosen action."""
    return all(resources.get(key, 0) >= amount
               for key, amount in cost.items())


def _building_value(game: Game, pid: str, item) -> float:
    """Estimate a building's permanent and remaining-round value."""
    card = game.cards[item.card_id]
    player = game.players[pid]
    remaining = game.max_rounds - game.round
    effect = card.effect
    bonus = 0.0
    if effect == "warden_hall":
        bonus = len(player.deployed)
    elif effect == "quest_power":
        # Power is a one-point threshold modifier, not a guaranteed
        # extra quest every round. A second Beacon does not stack.
        existing = any(
            game.cards[b.card_id].effect == "quest_power"
            for b in player.buildings
        )
        bonus = 0.0 if existing else min(3.0, remaining * 0.65)
    elif effect.startswith("produce:"):
        resource = effect.split(":", 1)[1]
        weight = {"crystal": 0.3, "ember": 0.25,
                  "aether": 0.35}[resource]
        bonus = remaining * weight
    elif effect == "rebate":
        bonus = min(2.5, remaining * 0.4)
    opportunity_cost = 0.3 * sum(card.cost.values())
    return card.prestige + bonus - opportunity_cost


def _best_building(game: Game, pid: str):
    """Return the most useful affordable building, if any."""
    player = game.players[pid]
    if len(player.buildings) >= 3:
        return None
    affordable = [
        item for item in game.blueprints
        if _affordable(
            player.resources, game.cards[item.card_id].cost
        )
    ]
    return max(
        affordable,
        key=lambda item: _building_value(game, pid, item),
        default=None,
    )


def _best_quest(game: Game, pid: str):
    """Choose a rewarding quest team without wasting ready dragons."""
    options = list(quest_options(game, pid))
    return max(
        options,
        key=lambda option: (
            option[2],
            -len(option[1]),
            -sum(game.cards[d.card_id].power + d.bond
                 for d in option[1]),
        ),
        default=None,
    )


def _best_bond(game: Game, pid: str):
    """Find an affordable bond with a useful scoring payoff."""
    player = game.players[pid]
    options = [
        dragon for dragon in player.deployed
        if dragon.bond < 3
        and _affordable(player.resources, BOND_COSTS[dragon.bond])
    ]
    if not options:
        return None, 0.0
    target = max(
        options,
        key=lambda dragon: (
            (0, 1, 2)[dragon.bond],
            value(game, dragon),
        ),
    )
    immediate = (0, 1, 2)[target.bond]
    # Stronger bonds help future quests; only completed levels
    # score permanent points, so don't overvalue early levels.
    future = 0.25 * max(0, game.max_rounds - game.round)
    return target, immediate + future


def value(game: Game, item) -> float:
    card = game.cards[item.card_id]
    ability_bonus = int(card.effect == "stone_guard")
    quest_bonus = {
        "storm_boost": 0.5,
        "shadow_bonus": 0.5,
        "flame_focus": 1.1,
        "tide_bounty": 0.45,
        "grove_bounty": 0.45,
    }.get(card.effect, 0.0)
    return card.prestige + 0.45 * card.power + ability_bonus + quest_bonus


def _team_value(game: Game, pid: str) -> float:
    """Evaluate current points and near-term quest opportunities."""
    immediate = game.score(pid)
    options = list(quest_options(game, pid))
    quest_value = max((reward for _, _, reward in options), default=0)
    return immediate + 0.4 * quest_value


def deploy_best(game: Game, pid: str) -> None:
    """Choose a deployment based on the whole team, not card rank."""
    player = game.players[pid]
    if not player.reserve or player.swapped:
        return
    if len(player.deployed) < 5:
        best = max(
            player.reserve,
            key=lambda dragon: value(game, dragon),
        )
        game.deploy(pid, best.uid)
        return

    baseline = _team_value(game, pid)
    selected = None
    best_gain = 0.0
    for incoming in player.reserve:
        for index, outgoing in enumerate(player.deployed):
            if outgoing.exhausted:
                continue
            player.deployed[index] = incoming
            try:
                gain = _team_value(game, pid) - baseline
            finally:
                player.deployed[index] = outgoing
            if gain > best_gain:
                best_gain = gain
                selected = (incoming.uid, outgoing.uid)
    if selected:
        game.deploy(pid, selected[0], selected[1])


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
                power = sum(
                    game.cards[d.card_id].power + d.bond
                    + (2 if game.cards[d.card_id].effect == "flame_focus"
                       else int(game.cards[d.card_id].effect == "storm_boost"))
                    for d in dragons
                ) + power_bonus
                power += int(prism and len(elements) >= 3)
                if (power >= req.get("power", 0)
                        and (not req.get("element")
                             or req["element"] in elements)
                        and len(elements) >= req.get("distinct", 0)):
                    shadow_bonus = sum(
                        game.cards[d.card_id].effect == "shadow_bonus"
                        for d in dragons
                    )
                    yield (
                        quest, dragons,
                        card.reward.get("prestige", 0) + shadow_bonus,
                    )


def _collector_development(game: Game, pid: str, building):
    """Spend Collector actions on dragons and points before stockpiling.

    Meditation is a blind draw in the current engine. Keep index zero
    without inspecting the order of the two hidden cards.
    """
    player = game.players[pid]
    remaining = game.max_rounds - game.round
    deck = game.decks["dragon"]
    needs_dragon = (
        remaining >= 2
        and len(player.deployed) < 5
        and not player.reserve
    )
    if needs_dragon and deck:
        next_card = game.cards[deck[-1]]
        recruit_cost = next_card.cost
        can_recruit = _affordable(player.resources, recruit_cost)
        can_meditate = (
            len(deck) >= 2 and player.resources["crystal"] >= 2
        )
        # Favor guaranteed recruitment when affordable and economical;
        # use the cheaper blind meditation for an expensive draw.
        expensive = recruit_cost.get("crystal", 0) >= 6
        reserve_crystal = player.resources["crystal"]
        if can_meditate and (
            not can_recruit
            or (expensive and reserve_crystal < 10)
        ):
            game.act(pid, "meditate", keep=0)
            return "meditate"
        if can_recruit:
            game.act(pid, "recruit")
            return "recruit"

    if building is not None:
        # A high-value building is still a better immediate use of
        # spare resources than a speculative bond.
        building_value = _building_value(game, pid, building)
        if building_value >= 3.0:
            game.act(pid, "build", uid=building.uid)
            return "build"

    if len(player.deployed) >= 4 or remaining <= 2 or not deck:
        dragon, bond_value = _best_bond(game, pid)
        if dragon is not None:
            build_value = (
                _building_value(game, pid, building)
                if building is not None else float("-inf")
            )
            if bond_value > build_value:
                game.act(pid, "bond", uid=dragon.uid)
                return "bond"

    if building is not None:
        game.act(pid, "build", uid=building.uid)
        return "build"
    return None


def choose_action(game: Game, pid: str, strategy: str) -> str:
    """Choose legal actions while balancing quest and setup value."""
    player = game.players[pid]
    quest = _best_quest(game, pid)
    building = _best_building(game, pid)

    # A Builder invests in useful permanent effects when they can
    # outweigh this turn's best quest. As the match ends, immediate
    # prestige becomes more important than future production.
    if strategy == "builder" and building is not None:
        value_now = _building_value(game, pid, building)
        quest_now = quest[2] if quest else 0
        if value_now >= quest_now + 0.6:
            game.act(pid, "build", uid=building.uid)
            return "build"

    if quest:
        item, dragons, _ = quest
        game.act(
            pid, "quest", uid=item.uid,
            dragons=[dragon.uid for dragon in dragons],
        )
        return "quest"

    # Builders use spare actions to strengthen dragons when the
    # available buildings add less value than a bond.
    if strategy == "builder":
        dragon, bond_value = _best_bond(game, pid)
        building_value = (
            _building_value(game, pid, building)
            if building is not None else float("-inf")
        )
        if dragon is not None and (
            building is None or bond_value > building_value
        ):
            game.act(pid, "bond", uid=dragon.uid)
            return "bond"

    if strategy in ("balanced", "builder") and building is not None:
        game.act(pid, "build", uid=building.uid)
        return "build"

    if strategy in ("bonding", "balanced"):
        candidates = [
            dragon for dragon in player.deployed
            if dragon.bond < 3
            and _affordable(
                player.resources, BOND_COSTS[dragon.bond]
            )
        ]
        if candidates:
            target = max(
                candidates,
                key=lambda dragon: (
                    dragon.bond,
                    value(game, dragon),
                ),
            )
            game.act(pid, "bond", uid=target.uid)
            return "bond"

    # Collector values a playable dragon, opportunistic meditation,
    # and lasting prestige over repeatedly banking unused Crystal.
    if strategy == "collector":
        collector_action = _collector_development(game, pid, building)
        if collector_action is not None:
            return collector_action

    if building is not None:
        game.act(pid, "build", uid=building.uid)
        return "build"

    # If useful construction is one resource away, channel it.
    if strategy == "builder" and len(player.buildings) < 3:
        candidates = sorted(
            game.blueprints,
            key=lambda item: _building_value(game, pid, item),
            reverse=True,
        )
        if candidates:
            cost = game.cards[candidates[0].card_id].cost
            deficits = {
                key: max(0, amount - player.resources.get(key, 0))
                for key, amount in cost.items()
            }
            target = max(
                deficits, key=deficits.get, default="aether"
            )
            if deficits.get(target, 0) > 0:
                gains = {target: 2}
                game.act(pid, "channel", gains=gains)
                return "channel"

    gains = (
        {"crystal": 2} if strategy == "collector" else
        {"ember": 2} if strategy == "bonding" else
        {"aether": 2} if strategy == "builder" else
        {"crystal": 1, "ember": 1}
    )
    game.act(pid, "channel", gains=gains)
    return "channel"


def score_breakdown(game: Game, pid: str) -> dict[str, int]:
    """Calculate additive scoring components matching Game.score."""
    player = game.players[pid]
    dragons = sum(
        game.cards[d.card_id].prestige
        + int(game.cards[d.card_id].effect == "stone_guard")
        for d in player.deployed
    )
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

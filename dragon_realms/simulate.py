"""Automated matches for the Dragon Realms rules engine.

Run: python -m dragon_realms.simulate --players 4 --games 100
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from random import Random

from .engine import Game, Phase
from .bots import choose_action, deploy_best, score_breakdown

STRATEGIES = ("balanced", "collector", "bonding", "builder")


@dataclass
class Result:
    seed: int
    scores: dict[str, int]
    winners: list[str]
    strategies: dict[str, str]
    events: list[dict]
    breakdowns: dict[str, dict[str, int]]


def _market_value(game: Game, pid: str, item,
                  strategy: str) -> float:
    """Estimate the long-term value of a public market card."""
    player = game.players[pid]
    card = game.cards[item.card_id]
    if card.kind == "relic":
        if len(player.relics) >= 2:
            return -1.0
        bonus = 2.5 if card.effect == "prism" else 0.0
        return card.prestige + bonus + (
            1.0 if strategy == "balanced" else 0.0
        )
    if len(player.reserve) >= 7:
        return -1.0
    elements = {
        game.cards[dragon.card_id].element
        for dragon in player.deployed
    }
    diversity = 2.5 if card.element not in elements else 0.0
    ability = {
        "storm_boost": 1.0,
        "stone_guard": 1.5,
        "shadow_bonus": 1.0,
    }.get(card.effect, 0.0)
    if card.effect.startswith("produce:"):
        turns_left = game.max_rounds - game.round
        ability = min(2.0, turns_left * 0.3)
    strategy_bonus = 2.0 if strategy == "collector" else 0.0
    full_team = len(player.deployed) >= 5
    existing = sorted(
        (
            game.cards[dragon.card_id].prestige
            for dragon in player.deployed
        )
    )
    weak = existing[0] if existing else 0
    replacement_cost = 2.0 if full_team and card.prestige <= weak else 0
    reserve_penalty = len(player.reserve) * 1.5
    return (
        card.prestige + 0.5 * card.power + diversity + ability
        + strategy_bonus - replacement_cost - reserve_penalty
    )


def _bid(game: Game, pid: str, strategy: str, rng: Random) -> None:
    """Select up to two useful bids within the available Crystal."""
    player = game.players[pid]
    budget = player.resources["crystal"]
    bids: dict[str, int] = {}
    ranked = sorted(
        game.market,
        key=lambda item: (
            _market_value(game, pid, item, strategy),
            rng.random(),
        ),
        reverse=True,
    )
    for item in ranked:
        if len(bids) >= 2:
            break
        value = _market_value(game, pid, item, strategy)
        card = game.cards[item.card_id]
        minimum = 3 if card.kind == "relic" else 2
        if value < minimum or budget < minimum:
            continue
        premium = 2 if value >= 6 else 1 if value >= 4 else 0
        amount = min(budget, minimum + premium)
        bids[item.uid] = amount
        budget -= amount
    game.submit_bids(pid, bids)


def _try_action(game: Game, pid: str, strategy: str) -> bool:
    player = game.players[pid]
    if strategy in ("builder", "balanced") and len(player.buildings) < 3:
        for item in list(game.blueprints):
            cost = game.cards[item.card_id].cost
            if all(player.resources.get(k, 0) >= v for k, v in cost.items()):
                game.act(pid, "build", uid=item.uid)
                return True
    if strategy in ("bonding", "balanced"):
        for item in sorted(player.deployed, key=lambda d: d.bond, reverse=True):
            if item.bond >= 3:
                continue
            cost = ({"ember": 2}, {"ember": 2, "aether": 1},
                    {"ember": 3, "aether": 2})[item.bond]
            if all(player.resources.get(k, 0) >= v for k, v in cost.items()):
                game.act(pid, "bond", uid=item.uid)
                return True
    if strategy == "collector" and len(player.reserve) < 7:
        if game.decks["dragon"]:
            card = game.cards[game.decks["dragon"][-1]]
            if all(player.resources.get(k, 0) >= v
                   for k, v in card.cost.items()):
                game.act(pid, "recruit")
                return True
    game.act(pid, "channel", gains={"ember": 1, "aether": 1})
    return True


def play_game(players: int = 4, seed: int = 0,
              strategies: tuple[str, ...] | None = None,
              rounds: int = 6) -> Result:
    """Play an entire match through the public engine API."""
    if not 3 <= players <= 6:
        raise ValueError("players must be between 3 and 6")
    chosen = strategies or tuple(
        STRATEGIES[i % len(STRATEGIES)] for i in range(players))
    if len(chosen) != players or any(s not in STRATEGIES for s in chosen):
        raise ValueError("Provide one valid strategy per player")
    ids = [f"player_{i + 1}" for i in range(players)]
    assignments = dict(zip(ids, chosen))
    game = Game(ids, seed=seed, max_rounds=rounds)
    rng = Random(seed + 1)
    for _ in range(rounds):
        assert game.phase == Phase.GATHER
        game.gather()
        for pid in game.priority():
            _bid(game, pid, assignments[pid], rng)
        game.resolve_market()
        # Trading requires negotiated consent; autonomous bots abstain for now.
        game.begin_actions()
        for pid in game.priority():
            player = game.players[pid]
            deploy_best(game, pid)
            while player.actions_left:
                choose_action(game, pid, assignments[pid])
        game.end_round()
    assert game.phase == Phase.FINISHED
    return Result(seed, game.scores(), game.winners(),
                  assignments, list(game.events),
                  {pid: score_breakdown(game, pid) for pid in ids})


def simulate(games: int = 100, players: int = 4, seed: int = 0,
             rounds: int = 6) -> dict:
    """Return reproducible aggregate results for multiple games."""
    if games < 1:
        raise ValueError("games must be positive")
    wins: Counter[str] = Counter()
    total_scores: Counter[str] = Counter()
    finished = 0
    components: dict[str, Counter[str]] = {}
    actions: dict[str, Counter[str]] = {}
    for index in range(games):
        rotation = index % players
        lineup = tuple(STRATEGIES[(seat + rotation) % len(STRATEGIES)]
                       for seat in range(players))
        result = play_game(players, seed + index, lineup,
                           rounds=rounds)
        finished += 1
        for pid, score in result.scores.items():
            strategy = result.strategies[pid]
            total_scores[strategy] += score
            components.setdefault(strategy, Counter()).update(
                result.breakdowns[pid])
        for event in result.events:
            if event["event"] == "action":
                strategy = result.strategies[event["player"]]
                actions.setdefault(strategy, Counter())[
                    event["action"]
                ] += 1
        for winner in result.winners:
            wins[result.strategies[winner]] += 1 / len(result.winners)
    counts = Counter()
    for index in range(games):
        for seat in range(players):
            counts[STRATEGIES[(seat + index % players) % len(STRATEGIES)]] += 1
    return {
        "games": finished,
        "players": players,
        "rounds": rounds,
        "seed": seed,
        "strategies": {
            strategy: {
                "appearances": count,
                "wins": round(wins[strategy], 3),
                "win_rate": round(wins[strategy] / count, 4),
                "average_score": round(
                    total_scores[strategy] / count, 2),
                "average_components": {
                    k: round(v / count, 2)
                    for k, v in sorted(components.get(strategy, {}).items())
                },
                "average_actions": {
                    action: round(
                        actions.get(strategy, Counter())[action] / count,
                        2,
                    )
                    for action in (
                        "quest", "build", "bond", "channel",
                        "recruit", "meditate",
                    )
                },
            }
            for strategy, count in counts.items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate Dragon Realms")
    parser.add_argument("--players", type=int, default=4)
    parser.add_argument("--games", type=int, default=100)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--rounds", type=int, default=8)
    parser.add_argument("--log", action="store_true",
                        help="Print event log for one game (requires --games 1)")
    args = parser.parse_args()
    if args.log:
        if args.games != 1:
            parser.error("--log requires --games 1")
        result = play_game(args.players, args.seed,
                           rounds=args.rounds)
        print(json.dumps({
            "scores": result.scores, "winners": result.winners,
            "strategies": result.strategies, "events": result.events,
            "breakdowns": result.breakdowns,
        }, indent=2, default=str))
    else:
        print(json.dumps(simulate(args.games, args.players, args.seed,
                                  rounds=args.rounds),
                         indent=2))


if __name__ == "__main__":
    main()

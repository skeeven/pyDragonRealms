"""Automated six-round matches for the Dragon Realms rules engine.

Run: python -m dragon_realms.simulate --players 4 --games 100
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from random import Random

from .engine import Game, Phase, RuleError

STRATEGIES = ("balanced", "collector", "bonding", "builder")


@dataclass
class Result:
    seed: int
    scores: dict[str, int]
    winners: list[str]
    strategies: dict[str, str]
    events: list[dict]


def _bid(game: Game, pid: str, strategy: str, rng: Random) -> None:
    player = game.players[pid]
    budget = player.resources["crystal"]
    bids: dict[str, int] = {}
    market = list(game.market)
    rng.shuffle(market)
    for item in market:
        card = game.cards[item.card_id]
        if card.kind == "relic" and len(player.relics) >= 2:
            continue
        if card.kind == "dragon" and len(player.reserve) >= 7:
            continue
        minimum = 3 if card.kind == "relic" else 2
        preference = (strategy == "collector" and card.kind == "dragon") or (
            strategy == "balanced" and card.kind == "relic")
        amount = minimum + (1 if preference else 0)
        if budget >= amount and len(bids) < 2:
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
              strategies: tuple[str, ...] | None = None) -> Result:
    """Play an entire match through the public engine API."""
    if not 3 <= players <= 6:
        raise ValueError("players must be between 3 and 6")
    chosen = strategies or tuple(
        STRATEGIES[i % len(STRATEGIES)] for i in range(players))
    if len(chosen) != players or any(s not in STRATEGIES for s in chosen):
        raise ValueError("Provide one valid strategy per player")
    ids = [f"player_{i + 1}" for i in range(players)]
    assignments = dict(zip(ids, chosen))
    game = Game(ids, seed=seed)
    rng = Random(seed + 1)
    for _ in range(6):
        assert game.phase == Phase.GATHER
        game.gather()
        for pid in game.priority():
            _bid(game, pid, assignments[pid], rng)
        game.resolve_market()
        # Trading requires negotiated consent; autonomous bots abstain for now.
        game.begin_actions()
        for pid in game.priority():
            player = game.players[pid]
            if player.reserve and not player.swapped:
                if len(player.deployed) < 5:
                    game.deploy(pid, player.reserve[0].uid)
                else:
                    candidate = max(
                        player.reserve,
                        key=lambda d: game.cards[d.card_id].prestige)
                    weakest = min(
                        player.deployed,
                        key=lambda d: game.cards[d.card_id].prestige)
                    if (game.cards[candidate.card_id].prestige >
                            game.cards[weakest.card_id].prestige and
                            not weakest.exhausted):
                        game.deploy(pid, candidate.uid, weakest.uid)
            while player.actions_left:
                _try_action(game, pid, assignments[pid])
        game.end_round()
    assert game.phase == Phase.FINISHED
    return Result(seed, game.scores(), game.winners(),
                  assignments, list(game.events))


def simulate(games: int = 100, players: int = 4, seed: int = 0) -> dict:
    """Return reproducible aggregate results for multiple games."""
    if games < 1:
        raise ValueError("games must be positive")
    wins: Counter[str] = Counter()
    total_scores: Counter[str] = Counter()
    finished = 0
    for index in range(games):
        result = play_game(players, seed + index)
        finished += 1
        for pid, score in result.scores.items():
            strategy = result.strategies[pid]
            total_scores[strategy] += score
        for winner in result.winners:
            wins[result.strategies[winner]] += 1 / len(result.winners)
    counts = Counter(
        STRATEGIES[i % len(STRATEGIES)] for i in range(players))
    return {
        "games": finished,
        "players": players,
        "seed": seed,
        "strategies": {
            strategy: {
                "appearances": games * count,
                "wins": round(wins[strategy], 3),
                "win_rate": round(wins[strategy] / (games * count), 4),
                "average_score": round(
                    total_scores[strategy] / (games * count), 2),
            }
            for strategy, count in counts.items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate Dragon Realms")
    parser.add_argument("--players", type=int, default=4)
    parser.add_argument("--games", type=int, default=100)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--log", action="store_true",
                        help="Print event log for one game (requires --games 1)")
    args = parser.parse_args()
    if args.log:
        if args.games != 1:
            parser.error("--log requires --games 1")
        result = play_game(args.players, args.seed)
        print(json.dumps({
            "scores": result.scores, "winners": result.winners,
            "strategies": result.strategies, "events": result.events,
        }, indent=2, default=str))
    else:
        print(json.dumps(simulate(args.games, args.players, args.seed),
                         indent=2))


if __name__ == "__main__":
    main()

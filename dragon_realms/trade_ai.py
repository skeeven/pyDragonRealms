"""Simple bot bargaining for voluntary resource trades.

Bots assess their own resource scarcity and may counter with fairer
quantities. Their holdings stay private from human opponents.
"""

from __future__ import annotations

from .engine import CAP, Game, Trade


def _resource_value(resources: dict[str, int], resource: str) -> float:
    """Value a unit by scarcity and its usefulness for acquisition."""
    base = 1.2 if resource == "crystal" else 1.0
    scarcity = max(0, 6 - resources[resource]) * 0.18
    return base + scarcity


def bot_accepts_trade(game: Game, bot: str, trade: Trade) -> bool:
    """Accept a resource offer when it improves the bot's position."""
    if trade.recipient != bot:
        return False
    if trade.give.get("cards") or trade.receive.get("cards"):
        return False
    offered = trade.give.get("resources", {})
    requested = trade.receive.get("resources", {})
    if not isinstance(offered, dict) or not isinstance(requested, dict):
        return False
    if len(offered) != 1 or len(requested) != 1:
        return False
    offered_kind, offered_amount = next(iter(offered.items()))
    requested_kind, requested_amount = next(iter(requested.items()))
    resources = game.players[bot].resources
    if offered_kind not in resources or requested_kind not in resources:
        return False
    if (
        offered_kind == requested_kind
        or type(offered_amount) is not int
        or type(requested_amount) is not int
        or not 1 <= offered_amount <= 3
        or not 1 <= requested_amount <= 2
        or resources[requested_kind] < requested_amount
        or resources[offered_kind] + offered_amount > CAP
    ):
        return False
    gain = offered_amount * _resource_value(resources, offered_kind)
    loss = requested_amount * _resource_value(resources, requested_kind)
    return gain >= loss * 1.05


def bot_counteroffer(
    game: Game,
    bot: str,
    proposer: str,
    offered_kind: str,
    requested_kind: str,
    offered_amount: int,
    requested_amount: int,
) -> tuple[int, int] | None:
    """Offer the closest acceptable quantity swap, if one exists."""
    if offered_kind == requested_kind:
        return None
    if offered_kind not in game.players[bot].resources:
        return None
    if requested_kind not in game.players[bot].resources:
        return None
    if game.players[bot].resources[requested_kind] < 1:
        return None

    proposer_resources = game.players[proposer].resources
    candidates = []
    for give_amount in range(1, 4):
        if proposer_resources[offered_kind] < give_amount:
            continue
        for get_amount in range(1, 3):
            if (give_amount, get_amount) == (
                offered_amount, requested_amount
            ):
                continue
            preview = Trade(
                id="preview",
                proposer=proposer,
                recipient=bot,
                give={"resources": {offered_kind: give_amount}},
                receive={"resources": {requested_kind: get_amount}},
            )
            if bot_accepts_trade(game, bot, preview):
                priority = (
                    abs(give_amount - offered_amount)
                    + 2 * abs(get_amount - requested_amount),
                    give_amount / get_amount,
                    give_amount,
                )
                candidates.append((priority, give_amount, get_amount))
    if not candidates:
        return None
    _, give_amount, get_amount = min(candidates)
    return give_amount, get_amount

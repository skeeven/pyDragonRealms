"""Simple, transparent bot responses to voluntary resource trades.

Only one-for-one resource swaps are evaluated here. The engine already
supports more sophisticated bilateral trades for future human matches.
"""

from __future__ import annotations

from .engine import Game, Trade


def bot_accepts_trade(game: Game, bot: str, trade: Trade) -> bool:
    """Accept an equal-sized swap that improves the bot's resource mix."""
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
    if (
        offered_kind == requested_kind
        or type(offered_amount) is not int
        or type(requested_amount) is not int
        or not 1 <= offered_amount <= 2
        or offered_amount != requested_amount
    ):
        return False
    resources = game.players[bot].resources
    if offered_kind not in resources or requested_kind not in resources:
        return False
    if resources[requested_kind] < requested_amount:
        return False
    if resources[offered_kind] + offered_amount > 20:
        return False
    # Prefer receiving something scarcer than what would be given away.
    return resources[offered_kind] < resources[requested_kind]

"""Versioned JSON snapshots for Dragon Realms games.

Snapshots are data, never executable Python objects. Do not use pickle for
uploaded saves.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from random import Random
from typing import Any

from .engine import (
    CAP,
    RESOURCES,
    Game,
    Instance,
    Phase,
    Player,
    RuleError,
    Trade,
    make_catalog,
)

SAVE_VERSION = 1
MAX_SAVE_BYTES = 1_000_000
ZONES = ("deployed", "reserve", "buildings", "relics")
BOARD_ZONES = ("market", "blueprints", "quests")
DECK_KINDS = ("dragon", "relic", "building", "quest")


def _as_json_state(value: Any) -> Any:
    """Convert nested random-state tuples to JSON-safe lists."""
    if isinstance(value, tuple):
        return [_as_json_state(item) for item in value]
    if isinstance(value, list):
        return [_as_json_state(item) for item in value]
    return value


def _as_tuple_state(value: Any) -> Any:
    """Restore nested tuples for random.Random.setstate."""
    if isinstance(value, list):
        return tuple(_as_tuple_state(item) for item in value)
    return value


def _valid_int(value: Any, minimum: int, maximum: int) -> bool:
    """Reject booleans and out-of-range integer values."""
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and minimum <= value <= maximum
    )


def _instance(data: Any, catalog: dict, kind: str) -> Instance:
    """Restore one card instance while checking its zone."""
    if not isinstance(data, dict):
        raise ValueError("A saved card must be an object")
    uid = data.get("uid")
    card_id = data.get("card_id")
    if not isinstance(uid, str) or not 1 <= len(uid) <= 128:
        raise ValueError("Invalid saved card identifier")
    if card_id not in catalog or catalog[card_id].kind != kind:
        raise ValueError("Saved card has the wrong type")
    bond = data.get("bond", 0)
    exhausted = data.get("exhausted", False)
    if not _valid_int(bond, 0, 3) or not isinstance(exhausted, bool):
        raise ValueError("Invalid saved card status")
    return Instance(
        uid=uid, card_id=card_id, bond=bond,
        exhausted=exhausted,
    )


def _cards(data: Any, catalog: dict, kind: str,
           maximum: int) -> list[Instance]:
    """Validate a saved zone of card instances."""
    if not isinstance(data, list) or len(data) > maximum:
        raise ValueError("Invalid saved card zone")
    return [_instance(item, catalog, kind) for item in data]


def _resources(data: Any) -> dict[str, int]:
    """Validate resource totals without coercing values."""
    if not isinstance(data, dict) or set(data) != set(RESOURCES):
        raise ValueError("Invalid saved resources")
    if not all(_valid_int(value, 0, CAP) for value in data.values()):
        raise ValueError("Saved resources are out of bounds")
    return dict(data)


def export_game(game: Game) -> str:
    """Create a portable snapshot containing all gameplay state."""
    snapshot = {
        "format": "dragon-realms",
        "version": SAVE_VERSION,
        "max_rounds": game.max_rounds,
        "round": game.round,
        "phase": game.phase.value,
        "order": list(game.order),
        "players": {
            pid: asdict(player) for pid, player in game.players.items()
        },
        "decks": {key: list(value) for key, value in game.decks.items()},
        "market": [asdict(item) for item in game.market],
        "blueprints": [asdict(item) for item in game.blueprints],
        "quests": [asdict(item) for item in game.quests],
        "bids": game.bids,
        "trades": {
            key: asdict(trade) for key, trade in game.trades.items()
        },
        "events": game.events,
        "game_version": game.version,
        "rng_state": _as_json_state(game.rng.getstate()),
    }
    return json.dumps(snapshot, indent=2, ensure_ascii=False)


def import_game(raw: str | bytes) -> Game:
    """Restore a validated game without executing uploaded contents."""
    if isinstance(raw, bytes):
        if len(raw) > MAX_SAVE_BYTES:
            raise ValueError("Save file is too large")
        raw = raw.decode("utf-8")
    if len(raw.encode("utf-8")) > MAX_SAVE_BYTES:
        raise ValueError("Save file is too large")
    try:
        data = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("Save file is not valid JSON") from exc
    if not isinstance(data, dict):
        raise ValueError("Save file must contain a JSON object")
    if (data.get("format") != "dragon-realms"
            or data.get("version") != SAVE_VERSION):
        raise ValueError("Unsupported Dragon Realms save version")

    order = data.get("order")
    players_data = data.get("players")
    max_rounds = data.get("max_rounds")
    current_round = data.get("round")
    if (not isinstance(order, list)
            or not 3 <= len(order) <= 6
            or not all(isinstance(pid, str) and pid for pid in order)
            or len(set(order)) != len(order)
            or not isinstance(players_data, dict)
            or set(players_data) != set(order)
            or not _valid_int(max_rounds, 3, 12)
            or not _valid_int(current_round, 1, max_rounds)):
        raise ValueError("Invalid saved players or round")
    try:
        phase = Phase(data["phase"])
    except (ValueError, KeyError):
        raise ValueError("Invalid saved game phase") from None
    if phase == Phase.FINISHED and current_round != max_rounds:
        raise ValueError("Finished save has an invalid round")

    catalog = make_catalog()
    game = Game.__new__(Game)
    game.cards = catalog
    game.max_rounds = max_rounds
    game.round = current_round
    game.phase = phase
    game.order = list(order)
    game.players = {}
    seen = set()

    def zone(raw_zone: Any, kind: str, limit: int) -> list[Instance]:
        cards = _cards(raw_zone, catalog, kind, limit)
        for item in cards:
            if item.uid in seen:
                raise ValueError("Duplicate card instance in save")
            seen.add(item.uid)
        return cards

    for pid in order:
        pdata = players_data[pid]
        if not isinstance(pdata, dict) or pdata.get("id") != pid:
            raise ValueError("Invalid saved player")
        player = Player(pid)
        player.resources = _resources(pdata.get("resources"))
        player.deployed = zone(pdata.get("deployed"), "dragon", 5)
        player.reserve = zone(pdata.get("reserve"), "dragon", 7)
        player.buildings = zone(pdata.get("buildings"), "building", 3)
        player.relics = zone(pdata.get("relics"), "relic", 2)
        for key in ("quest_prestige", "quests_completed"):
            value = pdata.get(key)
            if not _valid_int(value, 0, 100_000):
                raise ValueError("Invalid saved score")
            setattr(player, key, value)
        for key, limit in (
            ("actions_left", 2),
            ("auction_wins", 2),
        ):
            value = pdata.get(key)
            if not _valid_int(value, 0, limit):
                raise ValueError("Invalid saved player action state")
            setattr(player, key, value)
        for key in ("swapped", "rebate_used"):
            value = pdata.get(key)
            if not isinstance(value, bool):
                raise ValueError("Invalid saved player flag")
            setattr(player, key, value)
        game.players[pid] = player

    market_data = data.get("market")
    if not isinstance(market_data, list) or len(market_data) > 4:
        raise ValueError("Invalid saved market")
    game.market = []
    for item in market_data:
        if not isinstance(item, dict):
            raise ValueError("Invalid saved market")
        card_id = item.get("card_id")
        if card_id not in catalog:
            raise ValueError("Invalid market card")
        game.market.extend(zone([item], catalog[card_id].kind, 1))
    if len(game.market) > 4:
        raise ValueError("Invalid market size")
    game.blueprints = zone(data.get("blueprints"), "building", 3)
    game.quests = zone(data.get("quests"), "quest", 3)

    decks = data.get("decks")
    if not isinstance(decks, dict) or set(decks) != set(DECK_KINDS):
        raise ValueError("Invalid saved decks")
    game.decks = {}
    for kind in DECK_KINDS:
        cards = decks[kind]
        if not isinstance(cards, list) or len(cards) > len(catalog):
            raise ValueError("Invalid saved deck")
        if any(
            not isinstance(cid, str)
            or cid not in catalog
            or catalog[cid].kind != kind
            or cid.startswith("starter_")
            for cid in cards
        ):
            raise ValueError("Invalid saved deck contents")
        if len(set(cards)) != len(cards):
            raise ValueError("Duplicate card definition in deck")
        game.decks[kind] = list(cards)

    bids = data.get("bids", {})
    if not isinstance(bids, dict) or set(bids) - set(order):
        raise ValueError("Invalid saved bids")
    game.bids = {}
    market_uids = {item.uid for item in game.market}
    for pid, offers in bids.items():
        if not isinstance(offers, dict) or set(offers) - market_uids:
            raise ValueError("Invalid saved auction bids")
        if not all(_valid_int(v, 0, CAP) for v in offers.values()):
            raise ValueError("Invalid saved bid amount")
        if sum(offers.values()) > game.players[pid].resources["crystal"]:
            raise ValueError("Saved bids exceed player's resources")
        game.bids[pid] = dict(offers)

    trades = data.get("trades")
    if not isinstance(trades, dict) or len(trades) > 30:
        raise ValueError("Invalid saved trades")
    game.trades = {}
    for tid, trade_data in trades.items():
        if (not isinstance(tid, str)
                or not isinstance(trade_data, dict)
                or trade_data.get("id") != tid
                or trade_data.get("proposer") not in game.players
                or trade_data.get("recipient") not in game.players
                or trade_data.get("proposer") == trade_data.get("recipient")):
            raise ValueError("Invalid saved trade")
        for side_name in ("give", "receive"):
            side = trade_data.get(side_name)
            if not isinstance(side, dict):
                raise ValueError("Invalid saved trade contents")
            if set(side) - {"resources", "cards"}:
                raise ValueError("Invalid saved trade contents")
            resources = side.get("resources", {})
            cards = side.get("cards", [])
            if (not isinstance(resources, dict)
                    or set(resources) - set(RESOURCES)
                    or not all(_valid_int(v, 0, CAP)
                               for v in resources.values())
                    or not isinstance(cards, list)
                    or len(cards) > 9
                    or not all(isinstance(uid, str) and uid in seen
                               for uid in cards)):
                raise ValueError("Invalid saved trade contents")
        game.trades[tid] = Trade(
            id=tid,
            proposer=trade_data["proposer"],
            recipient=trade_data["recipient"],
            give=trade_data["give"],
            receive=trade_data["receive"],
        )
    version = data.get("game_version")
    events = data.get("events")
    if (not _valid_int(version, 0, 1_000_000)
            or not isinstance(events, list)
            or len(events) > 50_000
            or any(not isinstance(event, dict) for event in events)):
        raise ValueError("Invalid saved event history")
    game.version = version
    game.events = events

    game.rng = Random()
    try:
        game.rng.setstate(_as_tuple_state(data["rng_state"]))
    except (TypeError, ValueError, KeyError) as exc:
        raise ValueError("Invalid saved random state") from exc
    return game


def export_session(game: Game, bot_rng: Random,
                   auction: list[dict]) -> str:
    """Export a portable Streamlit session, including bot RNG state."""
    data = {
        "format": "dragon-realms-session",
        "version": SAVE_VERSION,
        "game": json.loads(export_game(game)),
        "bot_rng_state": _as_json_state(bot_rng.getstate()),
        "auction": auction,
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def import_session(raw: str | bytes) -> tuple[Game, Random, list[dict]]:
    """Restore a session after validating it as portable JSON."""
    if isinstance(raw, bytes):
        if len(raw) > MAX_SAVE_BYTES:
            raise ValueError("Save file is too large")
        raw = raw.decode("utf-8")
    if len(raw.encode("utf-8")) > MAX_SAVE_BYTES:
        raise ValueError("Save file is too large")
    try:
        data = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("Save file is not valid JSON") from exc
    if (not isinstance(data, dict)
            or data.get("format") != "dragon-realms-session"
            or data.get("version") != SAVE_VERSION):
        raise ValueError("Unsupported Dragon Realms session file")
    game = import_game(json.dumps(data.get("game")))
    rng = Random()
    try:
        rng.setstate(_as_tuple_state(data["bot_rng_state"]))
    except (TypeError, ValueError, KeyError) as exc:
        raise ValueError("Invalid saved bot random state") from exc
    auction = data.get("auction")
    if not isinstance(auction, list) or len(auction) > 100:
        raise ValueError("Invalid saved auction history")
    if not all(
        isinstance(item, dict)
        and isinstance(item.get("winner"), str)
        and isinstance(item.get("card"), str)
        and _valid_int(item.get("amount"), 0, CAP)
        for item in auction
    ):
        raise ValueError("Invalid saved auction history")
    return game, rng, auction

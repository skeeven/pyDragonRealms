"""Deterministic, framework-independent Dragon Realms rules engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from random import Random
from typing import Any
from uuid import uuid4


class RuleError(ValueError):
    """Raised when a player attempts an illegal move."""


class Phase(str, Enum):
    GATHER = "gather"
    MARKET = "market"
    TRADE = "trade"
    ACTIONS = "actions"
    END = "end"
    FINISHED = "finished"


ELEMENTS = ("Flame", "Tide", "Grove", "Storm", "Stone", "Shadow")
RESOURCES = ("crystal", "ember", "aether")
CAP = 20


@dataclass(frozen=True)
class Card:
    """Static card definition; instances are represented by unique IDs."""

    id: str
    kind: str
    name: str
    element: str = ""
    power: int = 0
    prestige: int = 0
    cost: dict[str, int] = field(default_factory=dict)
    effect: str = ""
    requirement: dict[str, Any] = field(default_factory=dict)
    reward: dict[str, int] = field(default_factory=dict)


@dataclass
class Instance:
    """Mutable card instance."""

    uid: str
    card_id: str
    bond: int = 0
    exhausted: bool = False


@dataclass
class Player:
    """Private player state."""

    id: str
    resources: dict[str, int] = field(default_factory=lambda: {
        "crystal": 5, "ember": 2, "aether": 2
    })
    deployed: list[Instance] = field(default_factory=list)
    reserve: list[Instance] = field(default_factory=list)
    buildings: list[Instance] = field(default_factory=list)
    relics: list[Instance] = field(default_factory=list)
    quest_prestige: int = 0
    quests_completed: int = 0
    actions_left: int = 2
    swapped: bool = False
    auction_wins: int = 0
    rebate_used: bool = False


@dataclass
class Trade:
    """Pending bilateral trade, atomically validated on acceptance."""

    id: str
    proposer: str
    recipient: str
    give: dict[str, Any]
    receive: dict[str, Any]


class Game:
    """Single-threaded authoritative state machine.

    An API adapter must serialize mutations per game. The engine has no I/O,
    networking, persistence, clock, or framework dependencies.
    """

    def __init__(self, player_ids: list[str], seed: int = 0):
        if not 3 <= len(player_ids) <= 6 or len(set(player_ids)) != len(player_ids):
            raise RuleError("Requires 3–6 distinct players")
        self.rng = Random(seed)
        self.players = {pid: Player(pid) for pid in player_ids}
        self.order = list(player_ids)
        self.rng.shuffle(self.order)
        self.cards = make_catalog()
        self.decks = {kind: [key for key, card in self.cards.items()
                             if card.kind == kind and not key.startswith("starter_")]
                      for kind in ("dragon", "relic", "building", "quest")}
        for deck in self.decks.values():
            self.rng.shuffle(deck)
        self.round = 1
        self.phase = Phase.GATHER
        self.market: list[Instance] = []
        self.blueprints: list[Instance] = []
        self.quests: list[Instance] = []
        self.bids: dict[str, dict[str, int]] = {}
        self.trades: dict[str, Trade] = {}
        self.events: list[dict[str, Any]] = []
        self.version = 0
        for player in self.players.values():
            for element in ("flame", "tide"):
                player.deployed.append(self._instance(f"starter_{element}"))
        self._refill(self.market, "dragon", 3)
        self._refill(self.market, "relic", 1)
        self._refill(self.blueprints, "building", 3)
        self._refill(self.quests, "quest", 3)

    def _instance(self, card_id: str) -> Instance:
        return Instance(uuid4().hex, card_id)

    def _draw(self, kind: str) -> Instance:
        if not self.decks[kind]:
            raise RuleError(f"{kind} deck empty")
        return self._instance(self.decks[kind].pop())

    def _refill(self, zone: list[Instance], kind: str, target: int) -> None:
        while sum(self.cards[item.card_id].kind == kind for item in zone) < target:
            if not self.decks[kind]:
                break
            zone.append(self._draw(kind))

    def _player(self, pid: str) -> Player:
        if pid not in self.players:
            raise RuleError("Unknown player")
        return self.players[pid]

    def _require(self, phase: Phase) -> None:
        if self.phase != phase:
            raise RuleError(f"Expected {phase.value} phase, got {self.phase.value}")

    def _find(self, items: list[Instance], uid: str) -> Instance:
        for item in items:
            if item.uid == uid:
                return item
        raise RuleError("Card not found in this zone")

    def _charge(self, player: Player, cost: dict[str, int]) -> None:
        for key, amount in cost.items():
            if key not in RESOURCES or amount < 0 or player.resources[key] < amount:
                raise RuleError("Insufficient resources or invalid cost")
        for key, amount in cost.items():
            player.resources[key] -= amount

    def _grant(self, player: Player, gains: dict[str, int]) -> None:
        for key, amount in gains.items():
            if key not in RESOURCES or amount < 0:
                raise RuleError("Invalid resource")
            player.resources[key] = min(CAP, player.resources[key] + amount)

    def _record(self, event: str, **data: Any) -> None:
        self.version += 1
        self.events.append({"version": self.version, "event": event, **data})

    def priority(self) -> list[str]:
        """Rotating first-player priority."""
        shift = (self.round - 1) % len(self.order)
        return self.order[shift:] + self.order[:shift]

    def gather(self) -> None:
        """Produce resources and advance to simultaneous sealed bidding."""
        self._require(Phase.GATHER)
        for player in self.players.values():
            gain = {"crystal": 2, "ember": 1, "aether": 1}
            for item in player.buildings + player.deployed:
                effect = self.cards[item.card_id].effect
                if effect.startswith("produce:"):
                    resource = effect.split(":", 1)[1]
                    gain[resource] += 1
            self._grant(player, gain)
        self.phase = Phase.MARKET
        self._record("gather")

    def submit_bids(self, pid: str, bids: dict[str, int]) -> None:
        """Replace a player's sealed bids; bid keys are market instance IDs."""
        self._require(Phase.MARKET)
        player = self._player(pid)
        if any(not isinstance(value, int) or isinstance(value, bool) or value < 0
               for value in bids.values()):
            raise RuleError("Bids must be nonnegative integers")
        if sum(bids.values()) > player.resources["crystal"]:
            raise RuleError("Total bids exceed available Crystal")
        for uid, amount in bids.items():
            card = self.cards[self._find(self.market, uid).card_id]
            minimum = 3 if card.kind == "relic" else 2
            if amount and amount < minimum:
                raise RuleError("Bid below minimum")
        self.bids[pid] = dict(bids)
        self._record("bid_submitted", player=pid)

    def resolve_market(self) -> None:
        """Resolve slots in order with rotating priority for ties."""
        self._require(Phase.MARKET)
        for item in list(self.market):
            eligible = []
            for pid in self.priority():
                player = self.players[pid]
                amount = self.bids.get(pid, {}).get(item.uid, 0)
                kind = self.cards[item.card_id].kind
                space = len(player.relics) < 2 if kind == "relic" else len(player.reserve) < 7
                if (amount > 0 and player.auction_wins < 2 and space
                        and player.resources["crystal"] >= amount):
                    eligible.append((amount, pid))
            if not eligible:
                continue
            best = max(amount for amount, _ in eligible)
            winner = next(pid for pid in self.priority()
                          if (best, pid) in eligible)
            player = self.players[winner]
            player.resources["crystal"] -= best
            if self.cards[item.card_id].kind == "relic":
                player.relics.append(item)
            else:
                player.reserve.append(item)
            player.auction_wins += 1
            if (not player.rebate_used and any(
                    self.cards[b.card_id].effect == "rebate"
                    for b in player.buildings)):
                self._grant(player, {"crystal": 1})
                player.rebate_used = True
            self.market.remove(item)
            self._record("auction_won", player=winner, card=item.uid, amount=best)
        self.bids.clear()
        self.phase = Phase.TRADE
        self._record("market_resolved")

    def propose_trade(self, pid: str, recipient: str, give: dict[str, Any],
                      receive: dict[str, Any]) -> str:
        self._require(Phase.TRADE)
        self._player(pid)
        self._player(recipient)
        if pid == recipient:
            raise RuleError("Cannot trade with yourself")
        if any(pid in (trade.proposer, trade.recipient)
               for trade in self.trades.values()):
            raise RuleError("Player already has a pending trade")
        self._validate_trade_side(self.players[pid], give)
        self._validate_trade_side(self.players[recipient], receive)
        trade = Trade(uuid4().hex, pid, recipient, give, receive)
        self.trades[trade.id] = trade
        self._record("trade_proposed", trade=trade.id)
        return trade.id

    def _validate_trade_side(self, player: Player, side: dict[str, Any]) -> None:
        if set(side) - {"resources", "cards"}:
            raise RuleError("Unknown trade field")
        cards = side.get("cards", [])
        if not isinstance(cards, list) or len(cards) > 4 or len(cards) != len(set(cards)):
            raise RuleError("Trade permits up to four distinct cards")
        owned = player.reserve + player.deployed + player.relics
        for uid in cards:
            item = self._find(owned, uid)
            if item.card_id.startswith("starter_") or item.exhausted:
                raise RuleError("Starter or exhausted dragon cannot be traded")
        resources = side.get("resources", {})
        for key, amount in resources.items():
            if (key not in RESOURCES or not isinstance(amount, int)
                    or isinstance(amount, bool) or amount < 0
                    or player.resources[key] < amount):
                raise RuleError("Invalid trade resources")

    def accept_trade(self, pid: str, trade_id: str) -> None:
        self._require(Phase.TRADE)
        trade = self.trades.get(trade_id)
        if trade is None or trade.recipient != pid:
            raise RuleError("Trade unavailable")
        proposer = self.players[trade.proposer]
        recipient = self.players[trade.recipient]
        self._validate_trade_side(proposer, trade.give)
        self._validate_trade_side(recipient, trade.receive)
        for player, incoming, outgoing in (
                (proposer, trade.receive, trade.give),
                (recipient, trade.give, trade.receive)):
            for key in RESOURCES:
                new_balance = (player.resources[key]
                               + incoming.get("resources", {}).get(key, 0)
                               - outgoing.get("resources", {}).get(key, 0))
                if new_balance > CAP:
                    raise RuleError("Trade exceeds resource cap")
        def destination(item: Instance, player: Player) -> list[Instance]:
            return player.relics if self.cards[item.card_id].kind == "relic" else player.reserve
        outgoing = []
        for source, target, side in ((proposer, recipient, trade.give),
                                     (recipient, proposer, trade.receive)):
            for uid in side.get("cards", []):
                item = self._find(source.reserve + source.deployed + source.relics, uid)
                outgoing.append((source, target, item))
        for player in (proposer, recipient):
            new_relics = len(player.relics) + sum(
                target is player and self.cards[item.card_id].kind == "relic"
                for _, target, item in outgoing) - sum(
                source is player and self.cards[item.card_id].kind == "relic"
                for source, _, item in outgoing)
            new_reserve = len(player.reserve) + sum(
                target is player and self.cards[item.card_id].kind == "dragon"
                for _, target, item in outgoing) - sum(
                source is player and item in player.reserve
                for source, _, item in outgoing)
            if new_relics > 2 or new_reserve > 7:
                raise RuleError("Trade exceeds card capacity")
        for source, target, side in ((proposer, recipient, trade.give),
                                     (recipient, proposer, trade.receive)):
            for key, amount in side.get("resources", {}).items():
                source.resources[key] -= amount
                target.resources[key] += amount
        for source, target, item in outgoing:
            for zone in (source.reserve, source.deployed, source.relics):
                if item in zone:
                    zone.remove(item)
                    break
            destination(item, target).append(item)
        del self.trades[trade_id]
        self._record("trade_accepted", trade=trade_id)

    def reject_trade(self, pid: str, trade_id: str) -> None:
        self._require(Phase.TRADE)
        trade = self.trades.get(trade_id)
        if trade is None or pid not in (trade.proposer, trade.recipient):
            raise RuleError("Trade unavailable")
        del self.trades[trade_id]
        self._record("trade_rejected", trade=trade_id)

    def begin_actions(self) -> None:
        self._require(Phase.TRADE)
        self.trades.clear()
        self.phase = Phase.ACTIONS
        self._record("actions_started")

    def deploy(self, pid: str, reserve_uid: str, deployed_uid: str | None = None) -> None:
        self._require(Phase.ACTIONS)
        player = self._player(pid)
        if player.swapped:
            raise RuleError("Already changed deployment this round")
        incoming = self._find(player.reserve, reserve_uid)
        outgoing = self._find(player.deployed, deployed_uid) if deployed_uid else None
        if outgoing and outgoing.exhausted:
            raise RuleError("Cannot swap an exhausted dragon")
        if not outgoing and len(player.deployed) >= 5:
            raise RuleError("Deployment full")
        player.reserve.remove(incoming)
        player.deployed.append(incoming)
        if outgoing:
            player.deployed.remove(outgoing)
            player.reserve.append(outgoing)
        player.swapped = True
        self._record("deployed", player=pid, card=reserve_uid)

    def act(self, pid: str, action: str, **kwargs: Any) -> None:
        """Execute one Warden action; adapter determines seat/action ordering."""
        self._require(Phase.ACTIONS)
        player = self._player(pid)
        if player.actions_left <= 0:
            raise RuleError("No actions remaining")
        if action == "channel":
            gains = kwargs["gains"]
            if (set(gains) - set(RESOURCES) or
                    any(not isinstance(v, int) or isinstance(v, bool) or v < 0
                        for v in gains.values()) or sum(gains.values()) != 2):
                raise RuleError("Channel grants exactly two resources")
            self._grant(player, gains)
        elif action == "bond":
            item = self._find(player.deployed, kwargs["uid"])
            if item.bond >= 3:
                raise RuleError("Maximum bond reached")
            costs = ({"ember": 2}, {"ember": 2, "aether": 1},
                     {"ember": 3, "aether": 2})
            self._charge(player, costs[item.bond])
            item.bond += 1
        elif action == "recruit":
            if len(player.reserve) >= 7:
                raise RuleError("Reserve full")
            if not self.decks["dragon"]:
                raise RuleError("Dragon deck empty")
            card = self.cards[self.decks["dragon"][-1]]
            self._charge(player, card.cost)
            player.reserve.append(self._draw("dragon"))
        elif action == "meditate":
            if len(player.reserve) >= 7 or len(self.decks["dragon"]) < 2:
                raise RuleError("Cannot meditate")
            keep = kwargs.get("keep", 0)
            if keep not in (0, 1):
                raise RuleError("Keep must be 0 or 1")
            self._charge(player, {"crystal": 2})
            drawn = [self._draw("dragon"), self._draw("dragon")]
            player.reserve.append(drawn[keep])
        elif action == "build":
            if len(player.buildings) >= 3:
                raise RuleError("Building capacity reached")
            item = self._find(self.blueprints, kwargs["uid"])
            self._charge(player, self.cards[item.card_id].cost)
            self.blueprints.remove(item)
            player.buildings.append(item)
            self._refill(self.blueprints, "building", 3)
        elif action == "quest":
            item = self._find(self.quests, kwargs["uid"])
            selected = kwargs["dragons"]
            if not 1 <= len(selected) <= 3 or len(set(selected)) != len(selected):
                raise RuleError("Choose 1–3 distinct dragons")
            dragons = [self._find(player.deployed, uid) for uid in selected]
            if any(dragon.exhausted for dragon in dragons):
                raise RuleError("Dragon already used for a quest")
            quest = self.cards[item.card_id]
            power = sum(self.cards[d.card_id].power + d.bond for d in dragons)
            if any(self.cards[b.card_id].effect == "quest_power"
                   for b in player.buildings):
                power += 1
            if (any(self.cards[r.card_id].effect == "prism" for r in player.relics)
                    and len({self.cards[d.card_id].element for d in dragons}) >= 3):
                power += 1
            elements = [self.cards[d.card_id].element for d in dragons]
            req = quest.requirement
            if (power < req.get("power", 0)
                    or (req.get("element") and req["element"] not in elements)
                    or len(set(elements)) < req.get("distinct", 0)):
                raise RuleError("Quest requirements not met")
            for dragon in dragons:
                dragon.exhausted = True
            player.quest_prestige += quest.reward.get("prestige", 0)
            player.quests_completed += 1
            self._grant(player, {k: v for k, v in quest.reward.items()
                                 if k in RESOURCES})
            self.quests.remove(item)
        else:
            raise RuleError("Unknown action")
        player.actions_left -= 1
        self._record("action", player=pid, action=action)

    def end_round(self) -> None:
        self._require(Phase.ACTIONS)
        self.phase = Phase.END
        self._refill(self.quests, "quest", 3)
        self._refill(self.market, "dragon", 3)
        self._refill(self.market, "relic", 1)
        if self.round in (3, 5):
            for kind in ("dragon", "relic"):
                stale = next((item for item in self.market
                              if self.cards[item.card_id].kind == kind), None)
                if stale:
                    self.market.remove(stale)
            self._refill(self.market, "dragon", 3)
            self._refill(self.market, "relic", 1)
        for player in self.players.values():
            player.actions_left = 2
            player.swapped = False
            player.auction_wins = 0
            player.rebate_used = False
            for item in player.deployed:
                item.exhausted = False
        if self.round == 6:
            self.phase = Phase.FINISHED
            self._record("finished", scores=self.scores())
        else:
            self.round += 1
            self.phase = Phase.GATHER
            self._record("round_started", round=self.round)

    def score(self, pid: str) -> int:
        player = self._player(pid)
        dragons = sum(self.cards[d.card_id].prestige + (0, 0, 1, 3)[d.bond]
                      for d in player.deployed)
        buildings = sum(self.cards[b.card_id].prestige for b in player.buildings)
        buildings += sum(min(5, len(player.deployed))
                         for b in player.buildings
                         if self.cards[b.card_id].effect == "warden_hall")
        relics = sum(self.cards[r.card_id].prestige for r in player.relics)
        for relic in player.relics:
            if self.cards[relic.card_id].effect == "ember_crown":
                relics += min(4, 2 * sum(
                    d.bond == 3 and self.cards[d.card_id].element == "Flame"
                    for d in player.deployed))
        elements = [self.cards[d.card_id].element for d in player.deployed]
        diversity = len(set(elements))
        # Starter dragons count for diversity, but not triple matching.
        nonstarter = [self.cards[d.card_id].element for d in player.deployed
                      if not d.card_id.startswith("starter_")]
        triples = any(nonstarter.count(element) >= 3 for element in ELEMENTS)
        synergy = max(3 if triples else 0, 5 if diversity >= 4 else 0,
                      8 if diversity >= 5 else 0)
        return player.quest_prestige + dragons + buildings + relics + synergy

    def scores(self) -> dict[str, int]:
        return {pid: self.score(pid) for pid in self.players}

    def winners(self) -> list[str]:
        self._require(Phase.FINISHED)
        def ranking(pid: str) -> tuple[int, int, int, int]:
            player = self.players[pid]
            return (self.score(pid), player.quests_completed,
                    sum(d.bond for d in player.deployed),
                    player.resources["crystal"])
        best = max(map(ranking, self.players))
        return [pid for pid in self.players if ranking(pid) == best]

    def view(self, viewer: str) -> dict[str, Any]:
        """Return a filtered view; other players' bids stay secret."""
        self._player(viewer)
        return {
            "round": self.round,
            "phase": self.phase.value,
            "version": self.version,
            "market": [i.__dict__.copy() for i in self.market],
            "quests": [i.__dict__.copy() for i in self.quests],
            "blueprints": [i.__dict__.copy() for i in self.blueprints],
            "my_bids": self.bids.get(viewer, {}).copy(),
            "players": {
                pid: {
                    "resources": player.resources.copy() if pid == viewer else None,
                    "deployed": [i.__dict__.copy() for i in player.deployed],
                    "reserve": ([i.__dict__.copy() for i in player.reserve]
                                if pid == viewer else len(player.reserve)),
                    "buildings": [i.__dict__.copy() for i in player.buildings],
                    "relics": [i.__dict__.copy() for i in player.relics],
                    "prestige": self.score(pid),
                }
                for pid, player in self.players.items()
            },
        }


def make_catalog() -> dict[str, Card]:
    """Create 102 deterministic original card definitions and two starters."""
    cards: dict[str, Card] = {}
    for element in ("Flame", "Tide"):
        key = f"starter_{element.lower()}"
        cards[key] = Card(key, "dragon", f"Starter {element}", element, 1)
    for element in ELEMENTS:
        for index in range(8):
            key = f"dragon_{element.lower()}_{index + 1}"
            power = 1 + index % 5
            effect = ("produce:ember" if element == "Flame" else
                      "produce:crystal" if element == "Tide" else
                      "produce:aether" if element == "Grove" else "")
            cards[key] = Card(key, "dragon", f"{element} Wyrm {index + 1}",
                              element, power, 1 + index % 4,
                              {"crystal": 2 + power}, effect)
    effects = ("produce:crystal", "produce:ember", "produce:aether",
               "warden_hall", "quest_power", "rebate")
    names = ("Crystal Observatory", "Ember Forge", "Aether Grove",
             "Warden Hall", "Quest Beacon", "Bazaar Archive")
    for index in range(18):
        key = f"building_{index + 1}"
        variant = index % 6
        cards[key] = Card(key, "building", f"{names[variant]} {index // 6 + 1}",
                          prestige=2 + index % 3,
                          cost={"aether": 2 + index % 4,
                                "crystal": index % 3}, effect=effects[variant])
    for index in range(24):
        key = f"quest_{index + 1}"
        element = ELEMENTS[index % 6]
        threshold = 5 + (index % 4) * 2
        cards[key] = Card(key, "quest", f"{element} Expedition {index // 6 + 1}",
                          requirement={"power": threshold, "element": element},
                          reward={"prestige": 3 + index % 5,
                                  RESOURCES[index % 3]: 1})
    relic_effects = ("prism", "ember_crown", "", "")
    for index in range(12):
        key = f"relic_{index + 1}"
        cards[key] = Card(key, "relic", f"Ancient Relic {index + 1}",
                          prestige=index % 3,
                          effect=relic_effects[index % 4])
    return cards
# Dragon Realms — Python Rules Engine

An original, framework-independent competitive fantasy card game engine.
No web UI, database, or third-party runtime packages are required.

## Quick start

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
```

## Example

```python
from dragon_realms import Game

game = Game(["alice", "bob", "cara"], seed=42)
game.gather()
card_id = game.market[0].uid
game.submit_bids("alice", {card_id: 3})
game.resolve_market()
game.begin_actions()
game.act("alice", "channel", gains={"crystal": 2})
print(game.view("alice"))
```

## Implemented

- Six-round phase state machine, 3–6 players, rotating priority
- 102 original main card definitions plus two starter definitions
- Independent shuffled decks, public market, buildings, and quests
- Resource production, caps, recruitment, bonding, channeling, meditation
- Sealed bidding with tie-breaks, two-win cap, capacity checks
- Bilateral atomic trading of cards and resources
- Deployment, quests, relic and building effects, scoring, tie-breaks
- Versioned event log and per-player redacted game views
- Seeded deck randomness for reproducible test setups

## Important prototype limitations

This is **engine v0.1**, not yet a complete release or formally balanced ruleset.
The 102 card definitions are programmatically generated placeholders, not a
hand-balanced final catalog. Cards for Stone, Storm, and Shadow do not yet have
unique special abilities. Activated relic timing, market card aging, full
turn-queue submission, and end-of-round timed resolution require refinement.

The API caller must serialize concurrent commands, enforce round-robin
turn ordering, persist snapshots, authenticate callers, and keep the seed
secret. The engine does not handle timers, authentication, persistence, or
networking. UUIDs are used for instance IDs; seeded randomness applies to
shuffled card definitions, not instance IDs.

For production, replace the mutable public `Game` API with an immutable
command/transition boundary, add full deterministic serialization and replay,
and ensure public views never expose hidden game metadata. The current
`view` hides other players' reserves and bids, but card definitions and
future private game fields will need an explicit visibility audit.

## Rules clarifications for v0.1

- Only deployed dragons count toward endgame dragon Prestige.
- Starter dragons are not tradable and count toward diversity, not triples.
- Quests must meet requirements or the action is rejected without cost.
- Meditate selects a drawn card by index 0 or 1; the other is discarded.
- Bids are resolved in public market slot order, with rotating tie priority.
- Missing bids are zero and trades expire when action phase starts.

See `dragon_realms/engine.py` for the authoritative implementation.

# Dragon Realms — Python Rules Engine

An original, framework-independent competitive fantasy card game engine.
No web UI, database, or third-party runtime packages are required.

## Quick start

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
```

## Streamlit visual prototype (v0.6)

```bash
python3 -m pip install -e '.[dev,ui]'
python3 -m pytest -q
python3 -m streamlit run app.py
```

Play a six-round match against three computer Wardens using a visual
scoreboard, sealed auctions, deployment, quest and building actions, and
contextual suggestions. The game lives in Streamlit session state; closing
or resetting the session loses the match. Save/resume, full card art, and
proper reveal-and-choose meditation are future work.

## Strategy tuning (v0.11)

The Builder bot estimates a building's **remaining-match value**, factoring
in power bonuses for future quests, production from future gather phases,
Warden Hall's deployed-dragon points, and construction cost. It can
prioritize a useful early investment over a smaller immediate quest.
Collector avoids spending actions to recruit when its five active slots
are already filled.

To compare against the 200-game eight-round v0.10 baseline, run:

```bash
python3 -m compileall -q dragon_realms app.py tests
python3 -m pytest -q
python3 -m dragon_realms.simulate --players 4 --games 200 --rounds 8
```

Baseline from the previous run (same 200 seeds): Balanced 35.5% wins,
Bonding 34.5%, Collector 22.5%, Builder 7.5%. Changes in win rates are
not proof of perfect balance; compare mean prestige and its components.
The bot heuristics changed, but card scoring rules did not.

## Smarter opponents and balance checks (v0.10)

Bots now rank auction cards based on usefulness, deployment space, elemental
diversity, and the remaining rounds. When their teams are full, they evaluate
the **whole team's prestige and quest opportunities** before swapping dragons.
They also avoid recruiting an unnecessarily large inactive reserve and can
switch to affordable buildings when their preferred action is unavailable.

Run a balance sample using the same eight-round format as the visual game:

```bash
python3 -m dragon_realms.simulate --players 4 --games 200 --rounds 8
```

The JSON report contains strategy win rates, average scores, and scoring
components. Results will fluctuate with sample size and game seeds. Use
several hundred games before drawing balance conclusions. This is a
first AI improvement pass, not evidence that the strategies are balanced.

## Dragon abilities (v0.9)

Nonstarter dragons now specialize by element:

- **Flame:** produce 1 Ember each gather phase.
- **Tide:** produce 1 Crystal each gather phase.
- **Grove:** produce 1 Aether each gather phase.
- **Storm:** gain 1 extra power while assigned to a quest.
- **Stone:** gain 1 additional prestige while deployed.
- **Shadow:** earn 1 additional quest prestige when assigned to a quest.

Effects apply per qualifying dragon. Starter Flame and Starter Tide do not
have special abilities. Quest guidance, bot selection, and score breakdowns
reflect these effects. This is a first balance pass, not a finalized ruleset.

## Guided quests and strategy (v0.8)

The Streamlit action panel now includes a Warden advisor, quest requirements,
ready-team suggestions, and explanations for unavailable quests.
Quest previews are read-only and use the same eligibility rules as the engine.
Completing a quest costs one action, gives the listed rewards, and exhausts
its selected dragons until the following round.

The advisor is a heuristic, not an optimal-play solver. It prioritizes
achievable quests and affordable buildings and adapts its context to early,
middle, and late game. Match length is selectable (6, 8, or 10 rounds, with
8 as the Streamlit default).

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

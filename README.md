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

Play an eight-round match by default against three computer Wardens
using a visual scoreboard, sealed auctions, deployment, quest and building
actions, and contextual suggestions. The game runs in Streamlit session
state; export a JSON save before closing the browser if you want to resume.
Detailed hand-painted card art and proper reveal-and-choose meditation are future work.

## Adaptive opponents and action diagnostics (v0.12)

Builder can strengthen dragons when quests or worthwhile buildings are
unavailable, instead of spending every spare action collecting resources.
Its building heuristic now discounts speculative production and quest-power
benefits, and it does not assign a second Quest Beacon an extra quest-power
bonus (the engine's effect does not stack).

The simulation report now includes **average_actions** for each strategy:
`quest`, `build`, `bond`, `channel`, `recruit`, and `meditate`.
These are measured from engine action events, not inferred from prestige.

```bash
git pull origin main
python3 -m compileall -q dragon_realms app.py tests
python3 -m pytest -q
python3 -m dragon_realms.simulate --players 4 --games 200 --rounds 8
```

The v0.11 baseline (200 games, seed 0, eight rounds) was Balanced
33.5%, Bonding 33.5%, Collector 24%, and Builder 9% wins. Builder's
average score was 41.73 and its average quest prestige was 12.07.
Compare the new action mix and scores before changing card rules.

## Complete dragon artwork collection (v0.26)

The final three collectible dragons now have registered full-size
illustrations and compact thumbnail artwork:

- **Obsidian** (Stone): black volcanic-glass scales in a lava field
- **Mountainborn** (Stone): immense stone guardian of alpine peaks
- **Nocturne** (Shadow): moonlit dragon with violet star-streaked wings

The collection now includes **50 of 50 dragon illustrations**:
48 named collectibles plus Starter Flame and Starter Tide.

Download the separate `dragon_realms_v026_artwork.zip` from the
ChatGPT handoff. This pack is incremental: it includes only the
three new portraits and their matching thumbnails. Keep the older
v0.20–v0.25 assets installed, then run:

```bash
git pull origin main
unzip -o ~/Downloads/dragon_realms_v026_artwork.zip -d .
python3 -m compileall -q dragon_realms app.py tests
python3 -m pytest -q
python3 -m streamlit run app.py
```

Artwork is optional at runtime. The SVG fallback still handles any
uninstalled files, and existing save files, scoring, and abilities
are unchanged. The 50 images are delivered in multiple art packs
rather than embedded in the GitHub code-only commits. You can commit
your locally installed `assets/dragons/` files to GitHub if you
want the artwork deployed with the game.

## Dragon artwork expansion — Batch 6 (v0.25)

The optional WebP artwork registry now covers **47 of 50 dragons
(94%)**, including the two starter dragons.

This batch adds eight collectible illustrations: **Abyssal, Verdant,
Wildbloom, Voltwing, Tempestral, Ironridge, Moonshade, and Voidscale**.
As before, every dragon has one Codex portrait and a face-focused
square thumbnail for the market, active board, and reserve.

Download the `dragon_realms_v025_artwork.zip` from the ChatGPT handoff.
This is an **incremental ZIP**, so retain your previous artwork
from v0.20–v0.24. From the project root:

```bash
git pull origin main
unzip -o ~/Downloads/dragon_realms_v025_artwork.zip -d .
python3 -m compileall -q dragon_realms app.py tests
python3 -m pytest -q
python3 -m streamlit run app.py
```

The final three collectible dragons awaiting portraits are
**Obsidian (Stone), Mountainborn (Stone), and Nocturne (Shadow)**.
They continue using the original SVG fallback. All card IDs,
mechanics, Codex counts, and save formats remain unchanged.
The WebP binaries are distributed in the downloadable ZIP rather
than committed through the GitHub text-file editor.

## Dragon artwork expansion — Batch 5 (v0.24)

The optional artwork system now supports **39 of 50 dragons
(78%)**, including both starter dragons.

The eight newly illustrated collectibles are **Blazehorn, Kindlefang,
Wavecaller, Foamwing, Bloomtail, Skyshiver, Cragheart, and Echofang**.
Each has a full WebP portrait for the Codex and a compact square
thumbnail for the market, reserve, and active dragon cards.

The `dragon_realms_v024_artwork.zip` contains only these eight new
portraits and their thumbnails (16 files), so extract it on top of
your existing v0.20–v0.23 artwork. From the repository root:

```bash
git pull origin main
unzip -o ~/Downloads/dragon_realms_v024_artwork.zip -d .
python3 -m compileall -q dragon_realms app.py tests
python3 -m pytest -q
python3 -m streamlit run app.py
```

Image files are supplied in the separate ZIP rather than the text-only
GitHub changes. The remaining 11 dragons use the original SVG
fallback until their portraits are ready. Card IDs, abilities, and
save-game compatibility are unchanged.

## Dragon artwork expansion — Batch 4 (v0.23)

The optional artwork registry now recognizes **31 of 50 dragon
illustrations (62%)**, including both starter dragons.

Eight new illustrations are available for **Pyrelash, Scorchscale,
Deepglide, Oakheart, Thundermaw, Galestrike, Slatehorn, and
Gloomwing**. Each has a full WebP portrait and a small square thumbnail
for market cards, deployed dragons, reserve, and the Codex.

This is a **separate incremental artwork pack**. Download
`dragon_realms_v023_artwork.zip` from the ChatGPT handoff and extract
it on top of the v0.20–v0.22 files:

```bash
git pull origin main
unzip -o ~/Downloads/dragon_realms_v023_artwork.zip -d .
python3 -m compileall -q dragon_realms app.py tests
python3 -m pytest -q
python3 -m streamlit run app.py
```

The remaining 19 collectible dragon cards continue using SVG
illustrations until their art is created. Card IDs, power, prestige,
abilities, auctions, scoring, and save formats remain unchanged.
The GitHub update includes mappings and tests; artwork binaries are
distributed in the ZIP for local installation.

## Dragon artwork expansion — Batch 3 (v0.22)

Eight new collectible dragon portraits have been added to the optional
artwork registry: **Ashmaw, Emberclaw, Coralcrest, Pearlscale,
Briarwing, Cloudbreaker, Boulderspine, and Umbraclaw**. Total coverage
is now **23 of 50 dragons**, including the two starters.

Download the separate `dragon_realms_v022_artwork.zip` and extract it
over your existing artwork from v0.20 and v0.21. This is an incremental
ZIP containing 16 WebP files, not an all-in-one replacement:

```bash
git pull origin main
unzip -o ~/Downloads/dragon_realms_v022_artwork.zip -d .
python3 -m compileall -q dragon_realms app.py tests
python3 -m pytest -q
python3 -m streamlit run app.py
```

Artwork file names are keyed by the original, unchanged dragon card IDs.
The SVG fallback still handles the other cards. Gameplay, balancing,
auction rules, Codex counts, and saved games are unchanged.

## Dragon artwork expansion — Batch 2 (v0.21)

Eight new dragons have full illustrations and compact thumbnails:
**Cinderwing, Riptalon, Mistfin, Thornroot, Fernwhisper, Sparkcrest,
Flintjaw, and Nightwhisper**. This brings the illustrated total to
15 of the 50 dragons (48 collectible cards plus 2 starters).
Every elemental family now has at least one illustrated collectible.

Install the additional v0.21 pack **on top of** your existing v0.20
images; this ZIP contains only the eight new portraits:

```bash
git pull origin main
unzip -o ~/Downloads/dragon_realms_v021_artwork.zip -d .
python3 -m compileall -q dragon_realms app.py tests
python3 -m pytest -q
python3 -m streamlit run app.py
```

Artwork uses the existing optional asset registry and SVG fallback
when a file is absent. Images are delivered in the separate ZIP and
may be committed to GitHub locally after installing. No changes to
gameplay, card data, Codex counts, or saved-game compatibility.

## Expanded dragon illustrations (v0.20)

Seven dragons now have illustrated portraits and matching card
thumbnails: **Starter Flame, Starter Tide, Infernos, Duskveil,
Mossback, Granitehide, and Stormspire**. The two starter dragons get
real artwork on every new match. Infernos and Duskveil add illustrated
collectibles from Flame and Shadow families. The existing three
portraits remain supported.

The artwork ZIP contains all seven portraits and their thumbnails.
Extract it over the repository root; it replaces previous v0.19 packs:

```bash
git pull origin main
unzip -o ~/Downloads/dragon_realms_v020_artwork.zip -d .
python3 -m compileall -q dragon_realms app.py tests
python3 -m pytest -q
python3 -m streamlit run app.py
```

Only four of the seven images are new in v0.20; three are carried
over from v0.19.1. All remaining dragon definitions still render using
SVG fallbacks. This is incremental artwork coverage, not the full
50-illustration target. Artwork files are delivered in a separate ZIP,
not the GitHub text-only commits. Card rules, stats, auctions, and save
formats are unchanged. The Codex still tracks 48 collectible dragons,
excluding the two starter dragons.

## Illustrated dragon portraits (v0.19)

The market, deployed/reserve cards, and Dragon Codex now support local
WebP illustrations through `dragon_realms/art_assets.py`. When a portrait
is available, it takes precedence over the existing SVG design. Missing
images automatically use the original SVG; no gameplay or save schema
changes are involved.

The first showcase art pack includes these files:

- `assets/dragons/stone/granitehide.webp`
- `assets/dragons/storm/stormspire.webp`
- `assets/dragons/grove/mossback.webp`

**Important:** The three binary portraits are provided as a separate
downloadable `dragon_realms_v019_artwork.zip` attachment, not yet committed
to GitHub. Download the ZIP and extract it into the repository root
(the ZIP contains the correct `assets/dragons/` structure):

```bash
unzip -o ~/Downloads/dragon_realms_v019_artwork.zip -d .
python3 -m pytest -q
python3 -m streamlit run app.py
```

If you want these images in GitHub as well, commit them after extraction:

```bash
git add assets/dragons/
git commit -m "art: add first three illustrated dragon portraits"
git push origin main
```

The Granitehide portrait is original generated artwork; Stormspire is a
crop from a generated concept; Mossback is an adapted painted portrait
and will eventually receive its own independently designed art. These
images are initial visual prototypes rather than the complete set of
48 finished illustrations.

## Artwork thumbnails and unique Mossback (v0.19.1)

Dragon artwork now supports two optional files for each illustrated
dragon: a face-focused square `-thumb.webp` for compact cards and an
uncropped `.webp` portrait for the larger Codex detail screen.
Missing thumbnails still use the original portrait, so the v0.19
artwork pack remains compatible. Missing portraits still use SVG.

The replacement Mossback illustration has green leaf scales, antler
branches, and an enchanted forest, rather than a green recolor of
Granitehide. Download `dragon_realms_v0191_artwork.zip` from the
ChatGPT handoff, then extract it at the repository root:

```bash
unzip -o ~/Downloads/dragon_realms_v0191_artwork.zip -d .
git pull origin main
python3 -m pytest -q
python3 -m streamlit run app.py
```

These image binaries are delivered in the ZIP rather than stored in the
code-only GitHub update. Once installed locally, commit the
`assets/dragons/**/*.webp` files if you want them available on other
devices. No scoring or save-format changes were made.

## Dragon Codex Gallery (v0.18)

The Codex now shows **eight compact gallery tiles** per element in a
four-column layout. Unknown dragons appear as small, locked silhouettes
instead of repetitive text descriptions. Discovered dragons show their
individual artwork and names, with a **View** button to open a larger
illustration, lore, power, prestige, and ability.

An elemental progress summary shows discoveries out of eight for all six
families, and the selected family has its own progress bar. The Codex
still tracks one match and uses the same card IDs and event history;
saves from v0.17 remain compatible. The feature is display-only and
does not affect auctions, quests, scoring, or simulations.

```bash
git pull origin main
python3 -m compileall -q dragon_realms app.py tests
python3 -m pytest -q
python3 -m streamlit run app.py
```

## Dragon Codex and individual identities (v0.17)

Every nonstarter dragon has a unique **name and short lore entry**.
Card definitions retain the original IDs, power, prestige, cost, and
elemental abilities; this is a collectible and visual update, not a
balance change. The six families now each have eight individual crest
and scale variations generated from the existing SVG artwork.

Open **Dragon Codex** beneath the active dragon board. Choose an
element to browse its eight entries. The Codex distinguishes:

- **Owned**: presently deployed or in your reserve.
- **Discovered**: previously acquired in the current match.
- **Unknown**: not yet acquired, with details hidden.

Discovered entries show their name, lore, and card statistics. New
auction, recruitment, and meditation events record card identifiers
so discoveries remain tracked during a match and across save/load.
Older save files remain readable; where older event history lacks
card identifiers, any currently held dragons still count as owned.
This first Codex tracks **one match**, not a permanent account-wide
collection spanning different matches.

```bash
git pull origin main
python3 -m compileall -q dragon_realms app.py tests
python3 -m pytest -q
python3 -m streamlit run app.py
```

## Final layout polish (v0.16.1)

Restores top spacing and a minimum title height so **Dragon Realms** is
fully visible below Streamlit's toolbar. Active and reserve dragon
cards now share the same five-column width, even when only one reserve
dragon is present.

The quest tab uses concise requirement, reward, and availability lines;
ready quests retain their action button and exact dragon team. The
**Save and resume** sidebar controls are still available inside a
collapsed expander, making more room for normal play. The compact
auction market introduced in v0.16 is unchanged.

Run the usual checks and launch the interface:

```bash
git pull origin main
python3 -m compileall -q dragon_realms app.py tests
python3 -m pytest -q
python3 -m streamlit run app.py
```

## Compact market and board (v0.16)

The market has a compact 2×2 grid of illustrated auction tiles. The
**Resolve auction** button now sits **above** the cards, so it remains
accessible even when the page is too short to show the complete grid.
Each tile shows dragon art, element, power, prestige, and a short ability
description. Bids still accept zero (pass) or the normal minimum of
2 Crystal for dragons and 3 for relics.

The five-slot dragon board is slightly shorter, resource metrics use less
padding, and the page starts closer to the top of the screen. Gameplay,
auction rules, strategy simulation, and save file compatibility are
unchanged.

```bash
git pull origin main
python3 -m compileall -q dragon_realms app.py tests
python3 -m pytest -q
python3 -m streamlit run app.py
```

## Elemental dragon artwork and card styling (v0.15)

The Streamlit game now renders original, self-contained SVG illustrations
for all six elemental dragon families: Flame, Tide, Grove, Storm, Stone,
and Shadow. They share a recognizable dragon silhouette, with unique
background sigils and color palettes for quick identification.

Illustrations appear in the five deployed dragon slots, reserve cards,
and market dragon listings. The cards remain small enough to fit a
single-screen game layout; exhausted dragons are dimmed. The artwork
is defined in `dragon_realms/artwork.py` and requires no network access,
third-party image hosting, or binary image files.

This is a stylized first artwork pass rather than individual art for
all 48 nonstarter dragon cards. Artwork changes do not alter gameplay,
scoring, or the v0.13 save format.

```bash
git pull origin main
python3 -m compileall -q dragon_realms app.py tests
python3 -m pytest -q
python3 -m streamlit run app.py
```

## Victory and match history (v0.14)

When the final round ends, Dragon Realms displays a winner announcement,
ranked prestige totals, the six scoring categories for every Warden,
and a timeline of key actions, deployments, and auction wins.

The leaderboard uses the same tie-breakers as the rules engine:
prestige, quests completed, total bond levels, and remaining Crystal.
The timeline supports filtering by round and includes richer card names
for games started with v0.14. Older saved matches still load and show
their existing event history; older events may not include card names.

Click **Play another match** on the finished screen to begin a fresh match
with the same round count and a new random seed. A new match replaces the
current in-browser game, so download a save first if you want to retain it.

```bash
git pull origin main
python3 -m compileall -q dragon_realms app.py tests
python3 -m pytest -q
python3 -m streamlit run app.py
```

## Save and resume (v0.13)

Use **Save and resume** in the Streamlit sidebar. Click **Download saved
game** to save a portable JSON file to your computer. To resume later,
open the app, upload the JSON file, and click **Restore uploaded game**.

A save retains the current round and phase, all player resources and cards,
auction state, quests, decks, score history, and the bot random-number
state. The saved data is independent of the browser session. You can
restore saved games at the market, actions, or finished scoreboard.

Save files contain gameplay data and may reveal opponents' hidden bids;
do not share them during a competitive match. Files are validated and
size-limited when loaded. This is **manual save/resume**, not automatic
cloud storage or autosave.

```bash
python3 -m compileall -q dragon_realms app.py tests
python3 -m pytest -q
python3 -m streamlit run app.py
```

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

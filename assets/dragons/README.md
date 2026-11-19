# Completed dragon art collection (v0.26)

The final three original fantasy-dragon portraits are distributed in
`dragon_realms_v026_artwork.zip`. Each has a full WebP portrait and
a compact square thumbnail:

| Dragon | Card ID | Portrait |
| --- | --- | --- |
| Obsidian | `dragon_stone_7` | `stone/obsidian.webp` |
| Mountainborn | `dragon_stone_8` | `stone/mountainborn.webp` |
| Nocturne | `dragon_shadow_8` | `shadow/nocturne.webp` |

Paths above are relative to `assets/dragons/`; thumbnail paths use
the same stem with `-thumb.webp`. Obsidian's card element is **Stone**
even though its design has lava and black volcanic-glass scales.
Mountainborn is a snow-capped alpine Stone dragon, and Nocturne is a
star-streaked moonlit Shadow dragon.

The new ZIP includes only these **six** files. Install it over the
previous v0.20–v0.25 packs, preserving all existing artwork:

```bash
git pull origin main
unzip -o ~/Downloads/dragon_realms_v026_artwork.zip -d .
python3 -m compileall -q dragon_realms app.py tests
python3 -m pytest -q
python3 -m streamlit run app.py
```

All **50 dragons** now have registered artwork (48 collectibles and
two starters). If an image file is not installed, the app still falls
back to its matching SVG automatically. No game rules or save-file
formats changed. The binaries ship in the downloadable ZIP, not the
GitHub code-only commits.

---

# Dragon artwork — Batch 6 (v0.25)

Eight more collectible portraits with square thumbnails are available
in `dragon_realms_v025_artwork.zip`:

| Dragon | Card ID | Portrait path |
| --- | --- | --- |
| Abyssal | `dragon_tide_8` | `tide/abyssal.webp` |
| Verdant | `dragon_grove_7` | `grove/verdant.webp` |
| Wildbloom | `dragon_grove_8` | `grove/wildbloom.webp` |
| Voltwing | `dragon_storm_6` | `storm/voltwing.webp` |
| Tempestral | `dragon_storm_7` | `storm/tempestral.webp` |
| Ironridge | `dragon_stone_6` | `stone/ironridge.webp` |
| Moonshade | `dragon_shadow_6` | `shadow/moonshade.webp` |
| Voidscale | `dragon_shadow_7` | `shadow/voidscale.webp` |

The paths above are relative to `assets/dragons/`. Each portrait
has a matching `-thumb.webp`. The v0.25 ZIP contains **16 WebP files**,
and is incremental: retain the v0.20–v0.24 artwork when installing.

```bash
git pull origin main
unzip -o ~/Downloads/dragon_realms_v025_artwork.zip -d .
python3 -m compileall -q dragon_realms app.py tests
python3 -m pytest -q
python3 -m streamlit run app.py
```

There are now 47 illustrated dragons out of 50, including the two
starters. Only **Obsidian, Mountainborn, and Nocturne** remain without
custom portraits. SVG fallback handles them safely. The artwork ZIP
is delivered separately from GitHub's code commits; game mechanics
and save compatibility are unchanged.

---

# Dragon artwork — Batch 5 (v0.24)

Eight additional collectible portraits and matching card thumbnails
are available in `dragon_realms_v024_artwork.zip`:

| Dragon | Card ID | Portrait path |
| --- | --- | --- |
| Blazehorn | `dragon_flame_6` | `flame/blazehorn.webp` |
| Kindlefang | `dragon_flame_7` | `flame/kindlefang.webp` |
| Wavecaller | `dragon_tide_5` | `tide/wavecaller.webp` |
| Foamwing | `dragon_tide_7` | `tide/foamwing.webp` |
| Bloomtail | `dragon_grove_6` | `grove/bloomtail.webp` |
| Skyshiver | `dragon_storm_5` | `storm/skyshiver.webp` |
| Cragheart | `dragon_stone_5` | `stone/cragheart.webp` |
| Echofang | `dragon_shadow_5` | `shadow/echofang.webp` |

Paths are relative to `assets/dragons/`. Each portrait has a
corresponding `-thumb.webp` with the same basename. This is an
**incremental art pack**, so retain your v0.20–v0.23 artwork:

```bash
git pull origin main
unzip -o ~/Downloads/dragon_realms_v024_artwork.zip -d .
python3 -m compileall -q dragon_realms app.py tests
python3 -m pytest -q
python3 -m streamlit run app.py
```

Total coverage is now 39 of 50 dragons: 37 collectible cards plus
the 2 starters. The other 11 collectible dragons still use SVG
fallbacks. Artwork does not change gameplay, save data, or card rules.
Only code and documentation are committed to GitHub; the actual
images are delivered in the separate ZIP.

---

# Dragon artwork — Batch 4 (v0.23)

Eight additional collectible portraits and matching face-focused
thumbnails are available in `dragon_realms_v023_artwork.zip`:

| Dragon | Card ID | Portrait path |
| --- | --- | --- |
| Pyrelash | `dragon_flame_3` | `flame/pyrelash.webp` |
| Scorchscale | `dragon_flame_5` | `flame/scorchscale.webp` |
| Deepglide | `dragon_tide_4` | `tide/deepglide.webp` |
| Oakheart | `dragon_grove_5` | `grove/oakheart.webp` |
| Thundermaw | `dragon_storm_3` | `storm/thundermaw.webp` |
| Galestrike | `dragon_storm_4` | `storm/galestrike.webp` |
| Slatehorn | `dragon_stone_4` | `stone/slatehorn.webp` |
| Gloomwing | `dragon_shadow_4` | `shadow/gloomwing.webp` |

Paths are relative to `assets/dragons/`. A `-thumb.webp` with the
same basename accompanies each portrait, for 16 WebP files in total.
This is an **incremental pack**. Retain v0.20, v0.21, and v0.22
artwork when extracting it:

```bash
git pull origin main
unzip -o ~/Downloads/dragon_realms_v023_artwork.zip -d .
python3 -m compileall -q dragon_realms app.py tests
python3 -m pytest -q
python3 -m streamlit run app.py
```

The registry now contains 31 illustrated dragon IDs out of 50:
29 of the 48 collectibles plus both starter dragons (62%).
Missing assets fall back to SVG. Rules, stats, and save formats are
unchanged. The images are delivered in the ZIP, not the code commits.

---

# Artwork expansion — Batch 3 (v0.22)

Eight additional dragon portraits and face-focused thumbnails are
provided in `dragon_realms_v022_artwork.zip`:

| Dragon | Card ID | Portrait |
| --- | --- | --- |
| Ashmaw | `dragon_flame_2` | `flame/ashmaw.webp` |
| Emberclaw | `dragon_flame_4` | `flame/emberclaw.webp` |
| Coralcrest | `dragon_tide_3` | `tide/coralcrest.webp` |
| Pearlscale | `dragon_tide_6` | `tide/pearlscale.webp` |
| Briarwing | `dragon_grove_4` | `grove/briarwing.webp` |
| Cloudbreaker | `dragon_storm_2` | `storm/cloudbreaker.webp` |
| Boulderspine | `dragon_stone_3` | `stone/boulderspine.webp` |
| Umbraclaw | `dragon_shadow_3` | `shadow/umbraclaw.webp` |

All paths are relative to `assets/dragons/`. Each portrait also
has a corresponding `-thumb.webp` file for the game board and market.
This pack is **incremental** and should be installed on top of the
v0.20 and v0.21 artwork packs.

```bash
git pull origin main
unzip -o ~/Downloads/dragon_realms_v022_artwork.zip -d .
python3 -m compileall -q dragon_realms app.py tests
python3 -m pytest -q
python3 -m streamlit run app.py
```

Total illustrated dragons: **23 of 50**, including two starters.
Other cards retain SVG fallback. The game engine, balance, card IDs,
collection tracking, and save files remain unchanged. Binary files
are distributed in the artwork ZIP, not committed to GitHub.

---

# Artwork expansion (v0.21)

Eight **additional** named dragon portraits are supplied in the
`dragon_realms_v021_artwork.zip` pack, each with a full WebP portrait
and a square `-thumb.webp` image:

| Dragon | Card ID | Relative asset path |
| --- | --- | --- |
| Cinderwing | `dragon_flame_1` | `flame/cinderwing.webp` |
| Riptalon | `dragon_tide_1` | `tide/riptalon.webp` |
| Mistfin | `dragon_tide_2` | `tide/mistfin.webp` |
| Thornroot | `dragon_grove_2` | `grove/thornroot.webp` |
| Fernwhisper | `dragon_grove_3` | `grove/fernwhisper.webp` |
| Sparkcrest | `dragon_storm_1` | `storm/sparkcrest.webp` |
| Flintjaw | `dragon_stone_2` | `stone/flintjaw.webp` |
| Nightwhisper | `dragon_shadow_2` | `shadow/nightwhisper.webp` |

**Keep the existing v0.20 pack installed**; v0.21 includes only these
eight additions, not the seven previous dragons. All 16 new WebP
files should be extracted into the project root:

```bash
unzip -o ~/Downloads/dragon_realms_v021_artwork.zip -d .
```

The same art registry and SVG fallbacks support all 15 illustrated
dragons. The gameplay engine, scoring, save files, and 48-card Codex
are unchanged. The image binaries are in the ZIP, not in GitHub's
text-file commits. Images are an initial generated-art pass, not final
commissioned illustrations.

---

# Dragon Realms portrait assets (v0.20)

The v0.20 artwork ZIP contains **seven distinct dragon illustrations**
and their matching thumbnail crops. It supersedes both previous packs,
so you only need to extract the latest ZIP.

| Dragon | Card ID | Files |
| --- | --- | --- |
| Starter Flame | `starter_flame` | `flame/starter_flame[-thumb].webp` |
| Starter Tide | `starter_tide` | `tide/starter_tide[-thumb].webp` |
| Infernos | `dragon_flame_8` | `flame/infernos[-thumb].webp` |
| Duskveil | `dragon_shadow_1` | `shadow/duskveil[-thumb].webp` |
| Mossback | `dragon_grove_1` | `grove/mossback[-thumb].webp` |
| Granitehide | `dragon_stone_1` | `stone/granitehide[-thumb].webp` |
| Stormspire | `dragon_storm_8` | `storm/stormspire[-thumb].webp` |

All paths are relative to `assets/dragons/`. The portrait uses
`name.webp` and the square card thumbnail uses `name-thumb.webp`.
The image renderer automatically selects the image when available and
falls back to the original SVG when it is not.

The 48 collectible dragons remain distinct from the two starter dragons.
Starter portraits are always visible on a normal game board, but the
Codex continues tracking only 48 collectible entries.

To install from the ZIP attached to the v0.20 ChatGPT handoff:

```bash
unzip -o ~/Downloads/dragon_realms_v020_artwork.zip -d .
```

No gameplay or save-file changes are required. The code was committed
to GitHub, but the actual binary WebP images are distributed in the ZIP.
You can commit `assets/dragons/*.webp` and nested folders to your
repository after extraction if you want the art to travel with the code.

---

# Dragon Realms artwork assets (v0.19.1)

WebP illustrations are optional. Each featured dragon has separate files
for a compact card thumbnail and its full Codex portrait:

| Dragon | Card thumbnail | Full portrait |
| --- | --- | --- |
| Granitehide | `stone/granitehide-thumb.webp` | `stone/granitehide.webp` |
| Stormspire | `storm/stormspire-thumb.webp` | `storm/stormspire.webp` |
| Mossback | `grove/mossback-thumb.webp` | `grove/mossback.webp` |

These are relative to `assets/dragons/`. Unzip the updated artwork
pack at the project root, replacing the old Mossback portrait.

Card thumbnails focus on the dragon's face. The Codex presents the
uncropped full image. If no thumbnail exists (including v0.19 packs),
the original portrait is used; if no portrait exists, the SVG remains
available. Each image is limited to 2 MB.

Mossback is a separate forest-dragon illustration with antlers and
leafy scales, extracted from an original generated concept rather
than recolored Granitehide art. The other two portraits remain as-is.

Artwork does not change gameplay, balance, or save formats.

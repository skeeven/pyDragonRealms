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

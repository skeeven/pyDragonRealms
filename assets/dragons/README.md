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

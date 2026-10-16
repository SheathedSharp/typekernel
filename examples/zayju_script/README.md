# ZayJu Letter Script

Florid English **letter-writing script** (花体信件书写体) for the brief phrase:

> zayju Discover everywhere

## Honest topology

This is **not** a slanted humanist/sans with `lean` / `oblique_font` / tracking.
Each glyph is a calligraphy **skeleton** (ovals, stems, entry/exit strokes)
expanded with a contrast broad-nib pen via
`typekernel.parts.skeleton.trace_letter`. Writing slant is baked into
centerline coordinates while drawing.

Charset: letters required by the brief (`a c d e h i j o r s u v w y z D`)
plus space. Semi-connected flourishes — not a full connected copperplate family.

## Build

```bash
pip install -e ".[compile,specimen,boolean]"
PYTHONPATH=src python examples/zayju_script/build.py
```

Outputs under `out/`:

| File | Role |
| --- | --- |
| `ZayJuLetterScript-Regular.otf` / `.ttf` | Installable Regular |
| `sentence_brief.png` | Brief phrase (filled composition, body) |
| `sentence_brief_display.png` | Brief phrase (filled composition, display) |
| `grid.png` | Used-letter inventory (from OTF) |
| `glyph_D.png` / `glyph_a.png` | Flourish / bowl checks |
| `ZayJuLetterScript-Regular.otf` | Installable; some apps rasterize dense expand outlines coarsely — prefer PNG proofs for review |

## Gates

`check_sentence_gate` / Controls L0 **do not apply** — this face is not derived
from `Controls.build_all`. Acceptance is visual (brief PNGs + OTF).

## Files

- `design.py` — metrics + per-glyph skeletons
- `build.py` — space, phrase kern, compile, proofs

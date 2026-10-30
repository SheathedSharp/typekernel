# B4 cold trial ACCEPTANCE — zayju forever young

**Date:** 2026-10-29 (America/Los_Angeles)  
**Tip installed:** typekernel @ `5e12903` (non-editable wheel into `~/code/tk-b4-cold-zayju/.venv`)  
**Project:** `hand/` via `tk new hand --starter script-roundhand --charset minimal --text "zayju forever young"`  
**Cold mode:** no reads of typekernel/src; public CLI + installed package only.

## Install honesty

```
pip show typekernel → Location: …/tk-b4-cold-zayju/.venv/lib/python3.14/site-packages
Editable: False
```

`tk doctor` initially MISSed `ufoLib2`/`ufo2ft`; fixed with `pip install 'typekernel[compile]'` (documented friction, not a glyph failure).

## Commands run

1. `tk new hand --starter script-roundhand --charset minimal --text "zayju forever young"`
2. `tk doctor` → OK after compile extra
3. `tk build .` → Hand-Italic.otf (14 glyphs in minimal scope)
4. `tk audit .` → **0 errors, 0 warnings** (info slits OK)
5. `tk audit --text "zayju forever young" .` → 0 errors, 0 warnings; join.rhythm_cv info OK
6. `tk read --text "zayju forever young" .` → no hard warns (near-tie INFO only)
7. `tk critique --text "zayju forever young" .` → see table
8. `tk proof --text "zayju forever young" .`

No glyph source edits were required; stock `script-roundhand` already met agent metrics after tip `5e12903`.

## `tk critique --text "zayju forever young"` (cited)

| signal | lvl | score | detail |
| --- | --- | --- | --- |
| evidence.review | info | n/a | no pass reviews yet |
| expect.changes | ok | 1.00 | expect keys=0 |
| contour.quality | ok | 1.00 | 0 contour warn(s), 2 info / 12 glyphs |
| read.identity | ok | 1.00 | 17/17 glyphs read; **0 hard warn(s)** |
| join.dy | ok | 1.00 | max Δy=**0.0** (threshold 20); 16 joined pairs |
| join.rhythm_cv | ok | 1.00 | gap CV=0.000 (threshold 0.35) |
| join.gap_dist | info | n/a | gaps n=16 mean=0 |

**critique warns=0 fails=0**

## Contour segment counts (public `session.glyph`)

| glyph | contours | segments |
| --- | --- | --- |
| o | 2 | 16 |
| z | 1 | 8 |
| a | 3 | 24 |
| n | 1 | 8 |
| e | 3 | 22 |
| y | 1 | 8 |
| g | 3 | 24 |

## Cold-agent success without source?

**Yes (agent metrics).** Scaffold + build + critique/read/audit all via public CLI. Starter Intent/Stroke/join already wired; cold user did not need to reverse-engineer library internals.

**Partial on aesthetics:** program identity/join/contour gates are green; whether the face *looks* like flowing letter-hand is **HUMAN-ONLY**.

## Human SCORE (blank — agent must not invent)

| SCORE | 1–5 |
| --- | --- |
| readable | |
| unified | |
| distinctive | |
| complete | |
| vision approve | |

## Remaining

- Human SCORE / vision approve
- Optional: agent may still iterate outlines for beauty without relaxing critique gates

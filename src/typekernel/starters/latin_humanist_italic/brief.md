# Brief — Latin Humanist Italic

Humanist true italic drawn with a **broad nib** (skeleton + `broad_nib`), not
contour Writer outlines. Medium calligraphic contrast, ~28° pen angle, Regular
weight, normal counter openness. Lean is first-class `System.slant` (~0.18).

## Typed intent

Declared in `system.py` as `BRIEF` / `INTENT` (`typekernel.system.intent`):

| Field | Value | Maps to |
| --- | --- | --- |
| contrast | medium | `tokens["pen_contrast"]` ≈ 0.52 (band 0.40–0.65) |
| slant | italic | `System.slant` ≈ 0.18 (band 0.10–0.24) |
| openness | normal | `n_width / stem[lc]` ≈ 5.55 (band 5.25–6.1) |
| weight | regular | `stem["lc"]` ≈ 72 (band 60–88) |
| pen_angle_deg | 28 | `tokens["pen_angle_deg"]` (±12°) |

`tk audit` warns when `system.py` drifts outside these bands. It does **not**
score beauty — use `tk proof`.

## Non-goals

- No heal / blend / seal.
- No aperture / roundness mega-knobs.
- Intent is not a glyph factory; letters stay in `glyphs/` + `elements.py`.

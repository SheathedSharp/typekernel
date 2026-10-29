# Brief — Latin Chancery

> **Quality note:** 结构示例，字形未通过视觉评审，不要当作字形质量范本。
>
> Structural example only — glyph shapes are **not** visually approved; do not treat this starter as a quality reference.


Chancery italic drawn with a **broad nib** (skeleton + `broad_nib`), not contour
Writer outlines. High calligraphic contrast, ~38° pen angle, Regular weight,
normal counter openness, and a first-class `System.slant` lean of 0.22.

## Typed intent

Declared in `system.py` as `BRIEF` / `INTENT` (`typekernel.system.intent`):

| Field | Value | Maps to |
| --- | --- | --- |
| contrast | high | `tokens["pen_contrast"]` = 0.28 (band 0.12–0.40) |
| slant | italic | `System.slant` = 0.22 (band 0.10–0.24) |
| openness | normal | `n_width / stem[lc]` ≈ 5.94 (band 5.25–6.1) |
| weight | regular | `stem["lc"]` = 64 (band 60–88) |
| pen_angle_deg | 38 | `tokens["pen_angle_deg"]` (±12°) |

`tk audit` warns when `system.py` drifts outside these bands. It does **not**
score beauty — use `tk proof`.

## Helpers

`elements.py` provides `pen_dot` (solid tittle/period), `flourish_entry` /
`flourish_exit`, `stroke_fragment`, `bowl` / `open_bowl`, and the slanted
vertical pen calibration. Reuse them instead of hand-rolling curls.

## Non-goals

- No heal / blend / seal.
- No aperture / roundness mega-knobs.
- Intent is not a glyph factory; letters stay in `glyphs/` + `elements.py`.

## Interpolation and VF safety

Interpolation mid-masters must keep topology and avoid self-intersections
under the slanted broad-nib expand. Several glyphs therefore use **intentional
gap / shallow / bar constructions** (e.g. B/P/D as rails, S/s as three bars,
bowl joins with ≥90 unit gaps, flourish tails replaced by gapped stubs). These
are structural VF-safe skeletons, not calligraphic finals — visual approval is
still required before treating shapes as house style.

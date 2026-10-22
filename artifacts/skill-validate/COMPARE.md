# Skill validate compare

Brief: *slightly wider geometric UI sans Regular, ASCII lowercase first* (SKILL.md).

| Recipe | Construction | OTF |
| --- | --- | --- |
| 1 | letter builders (`build_n` / `*_from_n` / `*_from_o`) — prefer yokes | `artifacts/skill-validate/recipe1_builders/SkillValidateUI-recipe1_builders.otf` |
| 2 | raw public yokes with **1.18×** `n_metrics.counter`, aperture **0.72**, longer `r` arm | `artifacts/skill-validate/recipe2_raw_yokes/SkillValidateUI-recipe2_raw_yokes.otf` |

Proofs: `proof_compare.png`, `proof_recipe1.png`, `proof_recipe2.png`, `proof_stems_large.png`.

## Structural

- Shared glyphs: `aefhilmnorstu`
- Topology signature differs on: `(none — same yoke recipes; metrics differ)`

## Visual

- **Look different? YES.** Recipe 2 reads wider on stem letters (`n` ink ≈+11%, `r` ≈+23%).
- **Stitch / kit-of-parts / missing-yoke on covered bodies? NO.** Lint clean; `n`/`h`/`m`/`u`/`r` are single continuous yoke contours. Small waterfall aliasing is not a seam.
- Recipe 2 still uses builders for `i`/`l`/`f`/`t`/`o` (no dedicated yoke in this script) — honest debt, not a fail on the yoke bar.

## Verdict

**PASS** — two Usage A skill recipes compile + proof; yokes usable; recipes look different by part params; italic-vf-construct untouched.

# Recipes (project edits)

## Heavier / lighter Regular

Edit `system.py` stems (`lc`, `uc`, …). Rebuild control proof. For VF, also scale Light/Bold via `tuned()`.

## Narrower face

Reduce `n_width` / `o_width` / `H_width` / `O_width` (and related `*_width` tokens) together; keep stem thickness unless brief asks otherwise. Re-proof `nnonoo` and `hamburgefonstiv`.

## Different corners

In `font.py`, swap `corners={"*": plain()}` for another corner plugin (e.g. slab) after installing/importing it from `typekernel.plugins.corners`. Glyph source hashes should stay stable for the same outlines（解耦试金石）.

## Fix a bad join

Open the glyph file under `glyphs/`. Adjust fragment geometry or overlap (stem + trough). **Do not** add a heal/blend/seal pass.

## Spacing

Edit `METRICS_KEYS` / `KERN_PAIRS` in `spacing.py`. `tk proof spacing` / `tk proof kern`.

## Audit follow-ups

`tk audit` warnings (stem vs System, zone overshoot) → change the named construction in the glyph, then re-audit. Direction / compat errors are hard failures.

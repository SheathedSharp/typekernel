# Recipes (project edits)

## Heavier / lighter Regular

Edit `system.py` stems (`lc`, `uc`, …). Rebuild control proof. For VF, also scale Light/Bold via `tuned()`.

## Narrower face

Reduce `n_width` / `o_width` / `H_width` / `O_width` (and related `*_width` tokens) together; keep stem thickness unless brief asks otherwise. Re-proof `nnonoo` and `hamburgefonstiv`.

## Different corners

In `project.py` (`PROJECT.corners`), swap `corners={"*": plain()}` for another corner plugin (e.g. slab) after installing/importing it from `typekernel.plugins.corners`. Glyph source hashes should stay stable for the same outlines（解耦试金石）.

## Fix a bad join

Open the glyph file under `glyphs/`. Adjust fragment geometry or overlap (stem + trough). **Do not** add a heal/blend/seal pass.

## Spacing

Edit `METRICS_KEYS` / `KERN_PAIRS` in `spacing.py`. `tk proof spacing` / `tk proof kern`.

## Audit follow-ups

`tk audit` warnings (stem vs System, zone overshoot) → change the named construction in the glyph, then re-audit. Direction / compat errors are hard failures.

## Look closer

```bash
tk proof --text "nnonoo HHOHOO"
tk proof --glyph n --size 320
tk pen --contrast 0.26 --angle 30 --out /tmp/pen.png
tk audit --overlap   # only when hunting cavities
```

## Italic slant (System field)

```python
system = System(..., slant=0.18, tokens={...})  # not tokens["slant"]
x, y = system.map_xy(100, 500)
bearing = system.stem_direction_deg()  # for oriented stem probes
```

`tk audit` and project `apply_spacing` read ``System.slant`` for italic-aware
vertical probes and mid-x-height sidebearing packing.

## Chancery flourishes

```bash
tk new mychancery --starter latin-chancery
```

Use `pen_dot`, `flourish_exit` / `flourish_entry` / `stroke_fragment` from the
copied `elements.py` — do not reimplement hook curls by hand.

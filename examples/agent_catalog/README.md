# Agent catalog — typekernel parts API

First consumer of this package is a **coding agent** that generates glyph
recipes; humans review specimens. Treat this page like Three.js’s geometry
list: pick a constructor, place it with transforms, boolean-join when needed,
bake metrics, export.

Install extras agents usually need:

```bash
pip install -e ".[boolean,specimen,compile,dev]"
```

## DesignContext (scene parameters)

| Constructor | One-liner |
| --- | --- |
| `DesignContext(...)` | Frozen family rhythm: stem, contrast, overshoot, roundness, tracking, aperture, … |
| `DesignContext.geometric_sans()` | Neo-grotesque preset (even colour, soft joins). |
| `DesignContext.humanist_sans()` | More contrast, open aperture. |
| `DesignContext.mono()` | Heavier stems, zero tracking. |
| `DesignContext.display()` | Thinner stems, loose tracking, larger overshoot. |
| `ctx.tuned(**fields)` | Copy with selected knobs overridden. |
| `ctx.thin` / `ctx.join_radius` | Derived horizontal thickness and fillet radius. |

## Primitives (Mesh / BufferGeometry analogs)

| Constructor | One-liner |
| --- | --- |
| `vertical_stem(ctx, x_left, y_bottom, y_top, *, width=None)` | Axis-aligned vertical stem rectangle. |
| `horizontal_bar(ctx, x_left, x_right, y_bottom, *, thickness=None)` | Axis-aligned bar. |
| `crossbar(ctx, x_left, x_right, y_center, *, thickness=None)` | Centered bar for `e` / `A` / `H`. |
| `rounded_rect(ctx, x0, y0, x1, y1, *, radius=None)` | Rectangle with corner fillets. |
| `capsule(ctx, x0, y0, x1, y1, *, radius=None)` | Stadium (soft bar / terminal). |
| `bowl(ctx, cx, cy, *, rx=None, ry=None, thickness=None)` | Elliptical ring → `(outer, counter)`. |
| `counter(ctx, cx, cy, rx, ry)` | Standalone elliptical hole. |
| `arch(ctx, x_left, x_right, y_bottom, y_top, *, thickness=None)` | n/h shoulder trough. |
| `shoulder(...)` | Alias for `arch`. |
| `u_bowl(ctx, x_left, x_right, y_top, y_bottom, *, thickness=None)` | U trough (two stems + round bottom). |
| `diagonal_stem(ctx, x0, y0, x1, y1, *, width=None, compensate=False)` | Thickened diagonal; `compensate=True` thins by angle vs vertical stem. |
| `stroke_polyline(ctx, points, *, width=None, join_radius=None)` | Centered stroke of a polyline with optional rounded joins. |
| `hook_terminal(ctx, x_center, y_top, y_bottom, *, hook_radius=None, width=None)` | Descender hook (j-like). |
| `tittle(ctx, cx, y_bottom, *, size=None)` | Dot for i/j. |
| `fillet_pad(ctx, x, y, *, radius=None, quadrant=0)` | Quarter-disk pad for stem/bowl joins (union afterward). |
| `terminal_ball(ctx, cx, cy, *, radius=None)` | Circular ball terminal. |
| `terminal_sheared(ctx, x0, y0, x1, y1, *, shear=0.35)` | Sheared cut-end parallelogram. |
| `serif_bracket(ctx, x_stem, y, *, side="left", length=None, thickness=None)` | Simple bracket serif stub. |
| `wedge(ctx, tip_x, tip_y, base_x0, base_y0, base_x1, base_y1)` | Triangle for traps / tapered cuts. |
| `ink_trap(ctx, apex_x, apex_y, *, depth, opening_deg, bisector_deg, size)` | Wedge trap tip-at-apex; subtract to open crotches. |
| `crotch_opener(ctx, apex, left_leg_deg, right_leg_deg, *, depth, size)` | Trap aimed from two leg bearings. |
| `crotch_join(left, right, ctx, *, apex, depth, size)` | Union legs + open crotch. |
| `apply_ink_trap(outline, trap)` | Boolean difference helper. |

## Transforms

| Constructor | One-liner |
| --- | --- |
| `translate(outline, dx, dy=0)` | Shift cubic outline. |
| `scale(outline, sx, sy=None, *, origin=(0,0))` | Scale about origin (uniform if `sy` omitted). |
| `rotate(outline, degrees, *, origin=(0,0))` | Rotate CCW about origin. |
| `mirror_x(outline, *, at_x=0)` / `mirror_y(..., at_y=0)` | Reflect across a line. |

## Boolean (optional `typekernel[boolean]`)

| Constructor | One-liner |
| --- | --- |
| `try_union(outlines)` | Union many outlines via skia-pathops. |
| `try_difference(a, b)` | `a − b`. |
| `try_intersection(a, b)` | Intersection. |
| `GlyphAssembler(...).union_solids()` | Union all solids at `build()`. |
| `GlyphAssembler(...).subtract_holes()` | Difference holes from solids at `build()`. |

Also: `typekernel.geo.boolean.boolean_op(a, b, "union"\|"difference"\|"intersection")`.

## Assembler + metrics

| Constructor | One-liner |
| --- | --- |
| `GlyphAssembler(ctx).add(o).add_hole(h).build()` | Pack sidebearings → `ComposedGlyph`. |
| `ComposedGlyph.solids / .holes / .advance / .context` | Baked ink + advance. |
| `KernPair(left, right, value)` | One pairwise kern. |
| `KernTable(pairs)` / `.lookup` / `.with_pair` | Tiny kerning table. |
| `default_sans_kern()` | Starter lowercase/display pairs. |
| `layout_glyphs(glyphs, names=None, *, tracking=None, kerning=None)` | Pen-x list with tracking + kern. |
| `sidebearing_for_width(ctx, ink_width)` | Heuristic sidebearing. |

## Latin recipes (starter glyphs)

| Constructor | One-liner |
| --- | --- |
| `letter_a/c/e/h/i/j/l/n/o/s/u/y/z(ctx)` | Lowercase recipes from shared parts. |
| `build_letter(ch, ctx=None)` | Dispatch by character. |
| `build_word(text, ctx=None)` | Shared-context word. |
| `word_zayju(ctx=None)` | Convenience for the demo word. |
| `LETTER_BUILDERS` | `dict[str, Callable]` of the above. |

## Minimal agent sketch

```python
from typekernel.parts import (
    DesignContext, GlyphAssembler, vertical_stem, arch, fillet_pad,
    layout_glyphs, default_sans_kern, build_word,
)

ctx = DesignContext.geometric_sans().tuned(stem=68, roundness=0.5)
n = (
    GlyphAssembler(ctx)
    .add(vertical_stem(ctx, 0, 0, ctx.x_height))
    .add(arch(ctx, ctx.stem, ctx.stem + 250, ctx.x_height * 0.45, ctx.x_height + ctx.overshoot))
    .add(vertical_stem(ctx, ctx.stem + 250, 0, ctx.x_height * 0.55))
    .add(fillet_pad(ctx, ctx.stem, ctx.x_height * 0.55, quadrant=0))
    .union_solids()
    .build()
)
glyphs = build_word("zayju", ctx)
xs = layout_glyphs(glyphs, list("zayju"), kerning=default_sans_kern())
```

## Honest gaps (so agents do not invent APIs)

- No full serif family — only `serif_bracket` stub.
- `ink_trap` / `crotch_opener` / `crotch_join` are real; `cleanup_joins(..., policy="ink_trap")` punches concave corners.
- `optics.stem.diagonal_compensation` / `measure_oriented_stem`; `diagonal_stem(..., compensate=True)`.
- No TrueType hinting, OpenType features, or mark positioning.
- Optical overshoot / stem measurement live under `typekernel.optics`, separate from parts.
- Path construction helpers (`arcTo`, `smoothCurveTo`, …) live on `typekernel.geo.PathBuilder`.

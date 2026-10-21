# Parts catalog (stable public surface)

Derived from `typekernel.parts` exports and related modules. **Do not invent APIs.**
Unstable / niche surfaces are marked. Units are design units on a typical 1000 UPM em unless noted.

Happy path: compose these → `Font.add_chars` / `add_char` → agent spacing → `build_font`.

## DesignContext (family proportions)

`from typekernel.parts import DesignContext`

| Field | Unit / type | Visual effect | Typical range | Copy-paste |
| --- | --- | --- | --- | --- |
| `units_per_em` | UPM | em square | 1000 | `DesignContext.geometric_sans()` |
| `x_height` | du | flat lowercase height | 480–560 | `.tuned(x_height=540)` |
| `cap_height` | du | flat caps | 680–740 | `.tuned(cap_height=700)` |
| `ascender` / `descender` | du | vertical window | asc ≈ cap; desc −180…−260 | `.tuned(ascender=750, descender=-220)` |
| `stem` | du | vertical stem thickness | 50–120 (Regular) | `.tuned(stem=88)` |
| `contrast` | ratio | thin = stem×contrast | 0.5–1.0 | `.tuned(contrast=0.85)` |
| `overshoot` | du | round extrema past flats | 8–16 | `.tuned(overshoot=12)` |
| `roundness` | 0..1 | join fillet ≈ roundness×stem | 0.15–0.45 | `.tuned(roundness=0.3)` |
| `tracking` | du | extra layout gap | 0–20 | `.tuned(tracking=4)` |
| `sidebearing_ratio` | fraction of x-height | default SB seed | 0.06–0.14 | `.tuned(sidebearing_ratio=0.09)` |
| `aperture` | 0..1 | open counters / terminals | 0.35–0.75 | `.tuned(aperture=0.6)` |
| `stress` | deg CCW | rotate thin axis on rounds | 0 default; try ±10…25 | `.tuned(stress=12)` |
| `terminal_style` | enum | open-stroke ends | `vertical`/`horizontal`/`angled`/`ball`/`flared` | `.tuned(terminal_style="angled")` |
| `italic_slant_deg` | deg | italic lean (0=upright) | 0 or ~8–12 | `.tuned(italic_slant_deg=10)` |
| `style` | `Style` | discrete topology switches | see below | `Style(a_form="double", serif="slab")` |

Presets: `geometric_sans()`, `humanist_sans()`, `code_clear()`, `display()`, `open_print()`, `paper_ink()`, `mono()`, `slab_serif()`, `bracketed_serif()`.

```python
ctx = DesignContext.humanist_sans().tuned(stem=82, aperture=0.62)
```

### Style (discrete topology)

`from typekernel.parts.style import Style`

| Field | Values | Effect |
| --- | --- | --- |
| `a_form` | `single` / `double` | single-storey vs double-storey a |
| `g_form` | `single` / `double` | single vs binocular g |
| `l_tail` | `none` / … | l terminal |
| `y_tail` | `straight` / … | y terminal |
| `i_dot` | `round` / … | tittle shape |
| `t_cut` | `flat` / … | t terminal cut |
| `serif` | `none` / `slab` / `bracketed` | serif voice |

## Primitives (`typekernel.parts.primitives`)

| Part | Returns | Key params | Visual | Copy-paste |
| --- | --- | --- | --- | --- |
| `vertical_stem` | Outline | `x_left,y_bottom,y_top`, `width=` | upright stem | `vertical_stem(ctx, 40, 0, ctx.x_height)` |
| `horizontal_bar` | Outline | `x_left,x_right,y_bottom`, `thickness=` | crossbar / arm | `horizontal_bar(ctx, 40, 300, 240)` |
| `crossbar` | Outline | centered bar | e/A bar | `crossbar(ctx, 40, 300, 280)` |
| `rounded_rect` | Outline | box + `radius=` | soft block | `rounded_rect(ctx, 0, 0, 100, 200, radius=12)` |
| `capsule` | Outline | stadium | soft stem | `capsule(ctx, 0, 0, 80, 400)` |
| `bowl` | `(outer, counter)` | `cx,cy`, `rx,ry`, `thickness(_v/_h)`, `shape`, `n`,`tension` | o-ring | `bowl(ctx, 200, 270, rx=160)` |
| `superellipse_ring` | `(outer, counter)` | `n`,`tension` | squircle ring | `superellipse_ring(ctx, 200, 270, n=2.5)` |
| `counter` | Outline | ellipse hole | raw counter | `counter(ctx, 200, 270, 100, 120)` |
| `arch` | Outline | shoulder block | n-arch mass | `arch(ctx, 100, 400, 200, 520)` |
| `shoulder` | Outline | join mass | n/h shoulder | `shoulder(ctx, 120, 380, 200, 500)` |
| `u_bowl` | Outline | U trough | u bottom | `u_bowl(ctx, 40, 400, 400, 0)` |
| `diagonal_stem` | Outline | endpoints, `width=`, `compensate=` | v/w/y legs | `diagonal_stem(ctx, 40, 0, 200, 500)` |
| `wedge` | Outline | tip + base | ink trap / serif wedge | `wedge(ctx, 100, 0, 80, 40, 120, 40)` |
| `serif_bracket` | Outline | `x_stem,y`, `side`, `length`, `thickness` | bracketed serif | `serif_bracket(ctx, 90, 0, side="left")` |
| `fillet_pad` | Outline | corner pad | soft join | `fillet_pad(ctx, 100, 100, quadrant=0)` |
| `ink_trap` / `apply_ink_trap` | Outline | apex + depth | crotch relief | `ink_trap(ctx, 200, 100, depth=20)` |
| `crotch_opener` / `crotch_join` | Outline | V join helpers | A/V crotch | `crotch_join(left, right, ctx)` |
| `hook_terminal` / `smooth_hook` | Outline | hook geometry | j/f hooks | `smooth_hook(ctx, 300, 400, 0)` |
| `terminal_ball` / `terminal_sheared` | Outline | end treatments | ball / shear ends | `terminal_ball(ctx, 300, 200)` |
| `tittle` | Outline | i/j dot | tittle | `tittle(ctx, 80, 600)` |
| `stroke_polyline` | Outline | point list + width | **unstable for weight** — demo only | prefer stems/bowls |

## Letter builders (control / related)

Built on primitives; return `ComposedGlyph`.

| Builder | From | Notable params | Copy-paste |
| --- | --- | --- | --- |
| `build_n` / `build_o` | context | optional `NMetrics`/`OMetrics` | `n = build_n(ctx)` |
| `h_from_n` `m_from_n` `u_from_n` `r_from_n` `i_from_n` `l_from_n` `j_from_n` | n | | `h_from_n(n, ctx)` |
| `f_from_n` `t_from_n` | n | `arm=` | `f_from_n(n, ctx, arm=0.82)` |
| `a_from_o` `b_from_o` `c_from_o` `d_from_o` `e_from_o` `g_from_o` `p_from_o` `q_from_o` `s_from_o` | o (+n) | `s_from_o(..., aperture=, width=, spine=)` | `s_from_o(o, ctx, aperture=0.6)` |
| `k_from_n` `v_from_n` `w_from_n` `x_from_n` `y_from_n` `z_from_n` | n | diagonals | `v_from_n(n, ctx)` |
| `build_H` `build_O` + `A_from_H`…`Z_from_O` | caps | | `H = build_H(ctx)` |

## Compose / boolean / transforms

| API | Role | Copy-paste |
| --- | --- | --- |
| `GlyphAssembler` | stack solids/holes → `ComposedGlyph` | see module docstring |
| `try_union` / `try_difference` / `try_intersection` | boolean (needs `[boolean]`) | `try_union(a, b)` |
| `heal_composed_glyph` | clean composed result | after boolean |
| `translate` `scale` `rotate` `mirror_x` `mirror_y` | outline transforms | `translate(outline, 10, 0)` |

## Terminals (`typekernel.parts.terminals`)

| API | Role |
| --- | --- |
| `ball_end` / `flat_end` / `hook_end` / `shear_end` | cut/treat an existing outline end |
| `*_terminal_piece` | standalone terminal solids |

## Metrics / spacing

| API | Role | Copy-paste |
| --- | --- | --- |
| `sidebearing_for_width` | SB from ctx ratio + ink width | `sidebearing_for_width(ctx, ink_w)` |
| `rhythm_from_control_glyphs` | target rhythm from n/o | `rhythm_from_control_glyphs(n, o)` |
| `auto_class_kern` / `auto_side_kern_classes` | class kern tables | after spacing |
| `layout_glyphs` | place a word | proof helper |
| `space_font` (`typekernel.optics.space`) | map of glyphs → spaced map | `space_font(drawn, ctx)` |

## Serifs / italic (family helpers)

| API | Stability | Role |
| --- | --- | --- |
| `apply_glyph_serifs` / `serif_metrics` (`parts.serifs`) | usable | attach slab/bracketed feet |
| `italic_design` / `italic_controls` (`parts.italic`) | usable; quality gated | construct italic masters |
| `oblique_font` (`compile.oblique`) | usable | **mechanical** slant — not Italic |

## Font + compile

| API | Role |
| --- | --- |
| `Font.from_context` / `add_char` / `add_chars` | font model |
| `Glyph.from_composed` / `for_char` | ComposedGlyph → Glyph |
| `build_font` / `build_variable_font` | binaries |
| `compose_font_from_controls` | **legacy** Controls → Font helper (default still runs unlock gates) |

## Legacy (not catalog happy path)

`Controls`, `DesignSequence`, `unlock_*`, `build_all` — still in tree for old examples/tests.
Do not document them as the way to design. Prefer parts + `Font` as above.

## Skeleton / pen (marked)

`Skeleton`, `trace_letter`, `Pen` / `expand` — useful for script experiments; **not** a weight axis.
See `examples/zayju_script/` and anti-patterns.

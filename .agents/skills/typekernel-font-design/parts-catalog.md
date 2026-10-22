# Parts catalog (stable public surface)

Derived from `typekernel.parts` exports. **Do not invent APIs.** Unstable /
niche surfaces are marked. Units are design units (du) on a typical 1000 UPM em
unless noted.

Happy path: **public yokes** (or letter builders that prefer them) →
`Font.add_chars` → agent spacing → `build_font`.

Every parameter below lists all five:

1. **name + unit**
2. **visual** (bigger / smaller)
3. **affects** (which parts / glyphs)
4. **range + breakage**
5. **copy-paste**

---

## DesignContext (family proportions)

`from typekernel.parts import DesignContext`

| Param | Unit | Visual bigger → / smaller → | Affects | Range + breakage | Copy-paste |
| --- | --- | --- | --- | --- | --- |
| `units_per_em` | UPM | larger em → coarser grid feel | whole font | keep **1000** unless you know why; odd UPM breaks tooling | `DesignContext.geometric_sans()` |
| `x_height` | du | taller flats / shorter | all lowercase bodies, yoke springs | **480–560** Regular; ≪480 cramped; ≫580 collisions with caps | `.tuned(x_height=540)` |
| `cap_height` | du | taller / shorter caps | `build_H`/`build_O` family | **680–740**; must stay above x-height + overshoot | `.tuned(cap_height=700)` |
| `ascender` | du | taller / shorter ascenders | `h`/`b`/`d`/`l`/`f`, `h_yoke` `stem_top` | ≈ cap or slightly above; ≪ cap clips | `.tuned(ascender=750)` |
| `descender` | du | deeper / shallower | `g`/`p`/`q`/`y`/`j`, bowl_stem descends | **−180…−260**; near 0 clips; ≪−300 wastes em | `.tuned(descender=-220)` |
| `stem` | du | heavier / lighter verticals | all stems, yoke `stem_width` default | Regular **50–120**; Bold often ×1.4–1.7; ≫140 pinches counters | `.tuned(stem=88)` |
| `contrast` | ratio | thinner horizontals / more mono | bowls (`thin=stem×contrast`), bars | **0.5–1.0**; ≪0.45 hairline breaks; >1 thickens thin | `.tuned(contrast=0.85)` |
| `overshoot` | du | rounder extrema past flats / flatter | bowls, yoke crowns | **8–16**; 0 looks flat; ≫20 collisions | `.tuned(overshoot=12)` |
| `roundness` | 0..1 | softer joins / sharper | join radius ≈ roundness×stem; u foot bulge | **0.15–0.45**; >0.6 blobs crotches | `.tuned(roundness=0.3)` |
| `tracking` | du | looser / tighter layout gap | `layout_glyphs` / space helpers | **0–20**; not a substitute for sidebearings | `.tuned(tracking=4)` |
| `sidebearing_ratio` | fraction of x-height | wider / tighter default SB | `sidebearing_for_width`, `space_font` | **0.06–0.14**; ≪0.05 collisions; ≫0.18 sparse | `.tuned(sidebearing_ratio=0.09)` |
| `aperture` | 0..1 | more open / more closed terminals | `c_yoke`/`e_yoke`/`s_yoke`, `*_from_o` openings | **0.35–0.75**; 0 seals; ~1 blows tip | `.tuned(aperture=0.6)` |
| `stress` | deg CCW | rotates thin axis on rounds | bowls / rings | **0** default; try **±10…25**; extreme warps | `.tuned(stress=12)` |
| `terminal_style` | enum | end cut recipe | open strokes (`c`/`e`/`r`/…) | `vertical`/`horizontal`/`angled`/`ball`/`flared` (`flared` stock = shear, not real flare) | `.tuned(terminal_style="angled")` |
| `italic_slant_deg` | deg | more / less lean | construct slant + branching topology (≥~6°) | **0** upright; italic **~8–12**; huge shear ruins joins | `.tuned(italic_slant_deg=10)` |
| `vf_compat_stem_segments` | bool | adds colinear stem knot on upright yokes | `n`/`h`/`m`/`r`/`u` yokes when True | True for upright `wght×ital` masters (TK-404); False on italic sheet | `.tuned(vf_compat_stem_segments=True)` |
| `vf_compat_oblique_splits` | bool | pre-splits for oblique VF | upright masters paired with italic | with `vf_italic_pair`; don’t flip casually | via `vf_upright_controls(...)` |
| `style` | `Style` | discrete topology | a/g form, serif kind, tails | see Style table | `Style(serif="slab", a_form="single")` |

Presets: `geometric_sans()`, `humanist_sans()`, `code_clear()`, `display()`,
`open_print()`, `paper_ink()`, `mono()`, `slab_serif()`, `bracketed_serif()`.

```python
ctx = DesignContext.humanist_sans().tuned(stem=82, aperture=0.62)
```

### Style (discrete topology)

`from typekernel.parts.style import Style`

| Param | Unit / values | Visual | Affects | Range + breakage | Copy-paste |
| --- | --- | --- | --- | --- | --- |
| `a_form` | `single`/`double` | single-storey vs binocular a | `a_from_o` / `a_yoke` path | stick to enum | `Style(a_form="double")` |
| `g_form` | `single`/`double` | single vs binocular g | `g_from_o` | stick to enum | `Style(g_form="single")` |
| `serif` | `none`/`slab`/`bracketed` | no / slab / bracketed feet | yoke `inline_serifs`, builders | slab/bracket prefer yokes with inline feet | `Style(serif="bracketed")` |
| `l_tail` / `y_tail` / `i_dot` / `t_cut` | enums | terminal / tittle variants | matching builders | stick to enum; unused = dead knob | `Style(i_dot="round")` |

---

## Continuous yokes (default letter bodies)

Prefer these over kit-of-parts + boolean for the same letter.

### Shared stem-yoke params (`shoulder_yoke` / `n_yoke` / `h_yoke` / `double_shoulder_yoke` / `u_yoke` / `r_yoke`)

| Param | Unit | Visual bigger → / smaller → | Affects | Range + breakage | Copy-paste |
| --- | --- | --- | --- | --- | --- |
| `x_left` | du | shifts body right / left | whole outline | usually **0.0** | `n_yoke(ctx, 0.0, ...)` |
| `counter` | du | wider / narrower counter | n/h/m/u/r width | ~**0.38–0.50×x_height**; ≤0 raises | `counter=ctx.x_height*0.42` |
| `stem_width` | du | heavier / lighter stems | left+right stems | defaults `ctx.stem`; ≤0 raises | `stem_width=ctx.stem` |
| `y_bottom` | du | raises / lowers baseline | feet | usually **0**; descenders negative | `y_bottom=0.0` |
| `stem_top` | du | taller / shorter left stem | n x-height; h ascender | n≈`x_height`; h≈`ascender` | `stem_top=ctx.x_height` |
| `shoulder_top` | du | higher / lower shoulder spring | `h_yoke` only | default `x_height` on h | `shoulder_top=ctx.x_height` |
| `join_y` | du | higher / lower crotch | inner shoulder join | keep below crown; italic clamps under `branch_y` | `join_y=None` (auto) |
| `crown_y` | du | taller / flatter outer crown | shoulder arch | ≈ x_height+overshoot; ≤spring breaks | `crown_y=None` |
| `leg_top` / `inner_crown` | du | right-leg / inner arch height | n family | leave `None` for auto; italic builders pass `None` | `leg_top=None` |
| `kappa` | float | rounder / tighter cubics | shoulder curves | ~**0.5–0.7**; extreme overshoots | `kappa=None` |
| `branch_y` | bool/float/None | True→mid-stem branch; float→abs y; None→upright | italic n/h/m/r/u | True ≈0.58×stem_top (h uses ascender recipe); with `inline_serifs` OK | `branch_y=True` |
| `written_feet` | bool | on→entry kick+exit outstroke | italic branching only | False when serifs replace kicks | `written_feet=True` |
| `inline_serifs` | bool | on→slab/bracket feet (caps upright) | stem yokes when `style.serif` slab/bracket | needs serif style; italic uses feet not kicks | `inline_serifs=True` |
| `soft_branch` | bool | on→fillet crotch; off→sharp then soften | `shoulder_yoke` / `n_yoke` | u italic uses False + `soften_stem_branch` | `soft_branch=True` |
| `vf_compat_stem` | bool | on→extra colinear stem knot | upright x-height stems (not needed on h spring) | for `vf_compat_stem_segments` masters | `vf_compat_stem=True` |

```python
from typekernel.parts import DesignContext, GlyphAssembler, n_yoke, h_yoke

ctx = DesignContext.humanist_sans()
n = GlyphAssembler(ctx).add(n_yoke(ctx, 0.0, counter=220, stem_width=ctx.stem)).build()
h = GlyphAssembler(ctx).add(h_yoke(ctx, 0.0, counter=220, stem_width=ctx.stem)).build()
# italic branching:
it = ctx.tuned(italic_slant_deg=10)
ni = GlyphAssembler(it).add(n_yoke(it, 0.0, branch_y=True)).build()
```

### `double_shoulder_yoke` (m)

Extra: `counter_scale` (float, default **0.92**) — smaller → tighter second counter;
affects `m` only; ≪0.7 pinches; ≫1.0 over-wide. Copy-paste:
`double_shoulder_yoke(ctx, 0.0, counter=220, counter_scale=0.92)`.

### `u_yoke`

Extra: `foot_bulge` (du | None) — bigger → deeper baseline toe; None follows
roundness recipe (0 when roundness≥0.35). Affects upright/italic `u`. Too large
self-intersects. Copy-paste: `u_yoke(ctx, 0.0, counter=220, foot_bulge=None)`.

### `r_yoke`

Extra: `arm` (0..1, default **0.55**) — bigger → longer truncated shoulder;
affects `r` only; must stay in **(0,1)** or raises. Copy-paste:
`r_yoke(ctx, 0.0, arm=0.55, counter=220)`.

### `bowl_stem_yoke` / `a_yoke`

| Param | Unit | Visual | Affects | Range + breakage | Copy-paste |
| --- | --- | --- | --- | --- | --- |
| `stem_left` | bool | True→b/p side; False→d/q | bowl+stem letters | — | `bowl_stem_yoke(ctx, stem_left=True)` |
| `descends` | bool | True→descender stem | p/q | needs room to descender | `descends=True` |
| `join` | float | higher / lower bowl–stem join | a/b/d/p/q | ~**0.75–0.9**; extreme overlaps | `join=0.85` |
| `stem_width` / `rx` / `ry` | du | stem / bowl radii | body | default ctx stem / o metrics | `rx=None` |
| `stem_top` | du | stem height | a to x-height; b/d ascender | — | `stem_top=ctx.x_height` |
| `top_exit` | bool | written exit on stem crown | italic single-storey a | serif usually False | `top_exit=True` |
| `inline_serifs` | bool | bracketed foot on stem | bowl_stem when bracketed | slab often separate | `inline_serifs=True` |

```python
from typekernel.parts import a_yoke, bowl_stem_yoke, GlyphAssembler
a = GlyphAssembler(ctx).add(a_yoke(ctx, join=0.85)).build()
b = GlyphAssembler(ctx).add(bowl_stem_yoke(ctx, stem_left=True)).build()
```

### Opening yokes `c_yoke` / `e_yoke` / `s_yoke`

| Param | Unit | Visual | Affects | Range + breakage | Copy-paste |
| --- | --- | --- | --- | --- | --- |
| `aperture` | 0..1 | more open / closed | c/e/s tip cut | default `ctx.aperture`; 0 seals | `c_yoke(ctx, aperture=0.6)` |
| `rx` / `ry` | du | wider/taller bowl | body | None → o metrics | `rx=None` |
| `bar_raise` (`e`) | float | higher / lower e bar | e eye | ~**0.15–0.35** | `e_yoke(ctx, bar_raise=0.25)` |
| `width` / `top_scale` / `spine` (`s`) | float | s width / top / spine y | s only | width~**0.75–0.9**; spine~**0.45–0.55** | `s_yoke(ctx, width=0.82, spine=0.5)` |

```python
from typekernel.parts import c_yoke, e_yoke, s_yoke, GlyphAssembler
GlyphAssembler(ctx).add(c_yoke(ctx, aperture=0.65)).build()
```

### `soften_stem_branch`

| Param | Unit | Visual | Affects | Range + breakage | Copy-paste |
| --- | --- | --- | --- | --- | --- |
| `stem_x` / `branch_y` | du | crotch location | post-sharp italic u (and helpers) | must hit line→curve join | see below |
| `stem` / `stem_top` | du | tolerance / drop scale | fillet radius | radius≈0.18×drop | |
| `tension` | float | tighter / looser blend | corner blend | default **0.95** | `tension=0.95` |

```python
from typekernel.parts import soften_stem_branch
outline = soften_stem_branch(outline, stem_x=ri, branch_y=by, stem=ctx.stem, stem_top=ctx.x_height)
```

---

## Italic strokes (`typekernel.parts.italic_strokes`)

| Part | Key params (5-field summary) | Copy-paste |
| --- | --- | --- |
| `emit_italic_entry_kick` | `l0` du (stem outer x); `stem` du thicker→bigger kick; `left_top` du climb; `y0` floor — affects PathBuilder left stem; bad `y0`>`left_top` collapses | `emit_italic_entry_kick(b, l0, stem=t, left_top=xh)` |
| `emit_italic_exit_outstroke` | `r0`/`r1` stem faces; `stem` — baseline exit; current point must be on `r1` | `emit_italic_exit_outstroke(b, r0, r1, stem=t)` |
| `emit_italic_branch_shoulder` | `branch_x`/`branch_y`; `shoulder0` cubic; `radius` — left-stem n/h/m/r only (not mirrored u) | used inside yokes; prefer `branch_y=True` |
| `italic_written_stem` | `x_left`; `stem`; `top`; `contrast_inset` — i/l written stem | `italic_written_stem(ctx, 0.0)` |
| `italic_kick_dims` | `stem` → `(dx,dy)` kick size | `dx, dy = italic_kick_dims(stem)` |

Stable for Usage A italic. Prefer yoke `branch_y` / builders over hand-emitting unless inventing a new letter.

---

## Compose / boolean

| Part | Params | Visual / affects / breakage | Copy-paste |
| --- | --- | --- | --- |
| `GlyphAssembler` | `.add` / `.add_hole` / `.union_solids` / `.subtract_holes` / `.build` | assembles any outlines into `ComposedGlyph` | `GlyphAssembler(ctx).add(n_yoke(...)).build()` |
| `soft_union` | `outlines: list`; `radius` du bigger→softer weld; `tension`; `ease`; `min_contour_area`; `heal` | stem+bar / serif stubs when **no yoke**; needs `[boolean]`; huge radius melts | `soft_union([stem, bar], radius=12)` |
| `try_union` / `try_difference` / `try_intersection` | two outlines | boolean ops; optional extra | `try_union(a, b)` |
| `heal_composed_glyph` | composed glyph | clean after boolean | after soft_union |

**Prefer a yoke over soft_union** whenever the letter body is already covered.

---

## Kit-of-parts primitives (fallback / invention)

Use when inventing shapes yokes don’t cover — not as the default for n/h/m/u/r/a/c/e/s.

| Part | Key params | Visual bigger→ | Affects | Breakage | Copy-paste |
| --- | --- | --- | --- | --- | --- |
| `vertical_stem` | `x_left,y_bottom,y_top`; `width=` | thicker stem | custom stems | width≤0 | `vertical_stem(ctx, 40, 0, ctx.x_height)` |
| `horizontal_bar` | `x_left,x_right,y_bottom`; `thickness=` | thicker bar | crossbars | — | `horizontal_bar(ctx, 40, 300, 240)` |
| `crossbar` | box + thickness | e/A bar | — | — | `crossbar(ctx, 40, 300, 280)` |
| `bowl` | `cx,cy`; `rx,ry`; `thickness(_v/_h)`; `shape`; `n`; `tension` | larger ring / thicker wall | o-like | rx/ry too small collapses hole | `bowl(ctx, 200, 270, rx=160)` |
| `superellipse_ring` | `n`,`tension` | squircle | display o | n≪2 wild | `superellipse_ring(ctx, 200, 270, n=2.5)` |
| `counter` | ellipse hole | larger hole | raw counters | — | `counter(ctx, 200, 270, 100, 120)` |
| `arch` / `shoulder` | box + thickness | taller shoulder mass | **prefer `shoulder_yoke` for letters** | — | `shoulder(ctx, 120, 380, 200, 500)` |
| `u_bowl` | trough box | deeper U | **prefer `u_yoke`** | — | `u_bowl(ctx, 40, 400, 400, 0)` |
| `diagonal_stem` | endpoints; `width=`; `compensate=` | thicker diagonal | v/w/y | — | `diagonal_stem(ctx, 40, 0, 200, 500)` |
| `wedge` / `ink_trap` / `apply_ink_trap` | apex + depth | deeper trap | crotches | depth too big eats stem | `ink_trap(ctx, 200, 100, depth=20)` |
| `crotch_join` / `crotch_opener` | join helpers | A/V crotch | diagonals | — | `crotch_join(left, right, ctx)` |
| `serif_bracket` | `x_stem,y`; `side`; `length`; `thickness` | longer foot | manual serifs; **prefer yoke `inline_serifs`** | — | `serif_bracket(ctx, 90, 0, side="left")` |
| `fillet_pad` | corner + quadrant | softer pad | joins | — | `fillet_pad(ctx, 100, 100, quadrant=0)` |
| `hook_terminal` / `smooth_hook` | hook geom | larger hook | j/f | — | `smooth_hook(ctx, 300, 400, 0)` |
| `terminal_ball` / `terminal_sheared` | end pieces | larger ball | terminals | — | `terminal_ball(ctx, 300, 200)` |
| `tittle` | position | larger dot | i/j | — | `tittle(ctx, 80, 600)` |
| `rounded_rect` / `capsule` | box + radius | — | soft blocks | — | `capsule(ctx, 0, 0, 80, 400)` |
| `stroke_polyline` | points + width | — | **unstable for weight** | sticky joins | prefer stems/bowls |

---

## Letter builders (prefer yokes)

Return `ComposedGlyph`. On Usage A they call public yokes (including italic,
slab/bracket `inline_serifs`, `vf_compat_stem`).

| Builder | From | Notable params | Copy-paste |
| --- | --- | --- | --- |
| `build_n` / `build_h` / `build_m` / `build_u` / `build_r` / `build_o` / `build_i` | context | optional metrics | `n = build_n(ctx)` |
| `h_from_n` `m_from_n` `u_from_n` `r_from_n` `i_from_n` `l_from_n` `j_from_n` | n | | `h_from_n(n, ctx)` |
| `f_from_n` `t_from_n` | n | `arm=`; `real_flare=` (opt-in tip) | `f_from_n(n, ctx, arm=0.82)` |
| `a_from_o` … `s_from_o` | o (+n for a) | `aperture=`, `real_flare=` | `s_from_o(o, ctx, aperture=0.6)` |
| `k_from_n` … `z_from_n` | n | diagonals | `v_from_n(n, ctx)` |
| `build_H` `build_O` + `A_from_H`… | caps | | `H = build_H(ctx)` |
| `A_yoke`…`Z_yoke` | cap Usage A (full Latin) | stem/bar, bowl, diagonal, hooks | `H_yoke(ctx)` / `B_yoke(ctx)` |

`real_flare=True` on some open builders: true tip widening via shear helper —
opt-in; stock `terminal_style="flared"` alone is still the shear recipe.
Prefer `apply_flare_terminal` when you want an explicit flare pass.

---

## Terminals / flare

| API | Params | Notes | Copy-paste |
| --- | --- | --- | --- |
| `apply_flare_terminal` | `at`; `amount` 0..1 bigger→more flare; `along` x/y; `inward`; `band` | **stable opt-in** real flare; not silent stock path | `apply_flare_terminal(ctx, outline, amount=0.35)` |
| `ball_end` / `flat_end` / `hook_end` / `shear_end` | cut existing tip | usable | `ball_end(outline, ...)` |
| `*_terminal_piece` | standalone solids | usable | |

---

## Serifs helpers

| API | Stability | Role | Copy-paste |
| --- | --- | --- | --- |
| yoke `inline_serifs=True` | **preferred** | feet drawn into continuous contour | `n_yoke(..., inline_serifs=True)` with `Style(serif="slab")` |
| `apply_glyph_serifs` | usable | boolean-attach feet from anchors | `apply_glyph_serifs(glyph)` |
| `serif_metrics` / inline path helpers | internal-ish | builders/yokes use these | prefer public yokes |

---

## Italic / VF helpers

| API | Stability | Role | Copy-paste |
| --- | --- | --- | --- |
| `italic_design` | usable | italic FormSources sheet (construct slant + lean) | `italic_design(FormSources.from_context(ctx))` |
| `vf_italic_pair` / `vf_upright_controls` | usable | matched upright+italic for `wght×ital` | `up, it = vf_italic_pair(FormSources.from_context(ctx))` |
| `oblique_font` (`compile.oblique`) | usable demo | **mechanical** slant — never ship as Italic | — |

Do **not** flip italic-VF construct flags casually; use `vf_italic_pair` as shipped.

---

## Metrics / spacing / transforms

| API | Role | Copy-paste |
| --- | --- | --- |
| `sidebearing_for_width` | SB from ctx ratio | `sidebearing_for_width(ctx, ink_w)` |
| `rhythm_from_control_glyphs` | rhythm from n/o | `rhythm_from_control_glyphs(n, o)` |
| `auto_class_kern` / `default_sans_kern` | kern tables | after spacing |
| `layout_glyphs` | place a word | proof helper |
| `space_font` (`typekernel.optics.space`) | glyph map → spaced | `space_font(drawn, ctx)` |
| `translate` `scale` `rotate` `mirror_x` `mirror_y` | outline transforms | `translate(outline, 10, 0)` |

---

## Font + compile

| API | Role |
| --- | --- |
| `Font.from_context` / `add_char` / `add_chars` | font model |
| `build_font` / `build_variable_font` | binaries |

---

## Marked unstable / not happy path

| Surface | Why |
| --- | --- |
| `Pen` / `expand` / `expand_polyline` / `stroke_polyline` as weight | sticky joins; not a master |
| `Skeleton` / `trace_letter` | script spikes only |
| `FormSources.build_all` / deleted `Controls` / `DesignSequence` / `unlock_*` | Usage B — dead |
| `compose_font` legacy FormSources helper | not Usage A design |
| `arch`/`shoulder`/`u_bowl` kit for n/u | use yokes instead |
| Private `control._*` | do not call from agent scripts |

## Caps / figures / punct / diacritics

Exported (`A_from_H`…, `tabular`, punct/diacritic modules) — usable; not every
param is exhaustively tabled here. Compose from `build_H`/`build_O` + related
forms; same Usage A exit. If a param is undocumented, read the docstring — do
not invent.


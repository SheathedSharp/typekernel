# Recipes (parts only — no aggregate APIs)

All recipes assume Usage A: compose → `Font` → space → compile → proof.
Do **not** reach for deleted `Controls` / `build_all` / `DesignSequence` / `unlock_*`.

Default continuous path = **public yokes** (or letter builders that prefer them).

## Fatten (heavier master)

**Which parts:** new `DesignContext.stem` (+ usually tighter `aperture` / counters);
recompose every glyph with the same yokes/builders on that context. Optional
`with_stem_relief()` on the context when weight ladders pinch.

```python
from typekernel.parts import DesignContext, build_n, build_o, m_from_n

reg = DesignContext.humanist_sans()
bold = reg.tuned(stem=reg.stem * 1.55, aperture=0.5)
n_b, o_b = build_n(bold), build_o(bold)   # yokes under the hood
m_b = m_from_n(n_b, bold)
# rebuild the rest of the charset on `bold`, then space_font → Font — separate master
```

Raw yoke path: `n_yoke(bold, 0.0, stem_width=bold.stem, counter=...)`.

**Do not:** `expand` / stroke inflate a Regular outline and call it Bold.

## Contrast (thick/thin)

**Which parts:** `DesignContext.contrast` and `stress`; bowls / opening yokes
read `stem` vs `thin=stem×contrast`. Stem yokes stay on `stem_width`.

```python
from typekernel.parts import DesignContext, bowl, e_yoke, GlyphAssembler

ctx = DesignContext.humanist_sans().tuned(contrast=0.72, stress=8.0)
outer, hole = bowl(ctx, 200, 270)  # thickness_v/h follow stem/thin
e = GlyphAssembler(ctx).add(e_yoke(ctx, aperture=ctx.aperture)).build()
```

Regression notes: `tests/parts/test_stress.py`, `tests/parts/test_knob_coverage.py`.

## Serif foot / bracketed serif

**Which parts (preferred):** `Style.serif` + yoke / builder `inline_serifs`
(builders pass this automatically when `style.serif` is slab/bracket).

```python
from typekernel.parts import DesignContext, GlyphAssembler, n_yoke, build_n
from typekernel.parts.style import Style

ctx = DesignContext.slab_serif()  # or .tuned(style=Style(serif="bracketed"))
n = build_n(ctx)  # continuous n_yoke + inline feet
# raw:
n2 = GlyphAssembler(ctx).add(
    n_yoke(ctx, 0.0, counter=220, inline_serifs=True)
).build()
```

Italic × serif: same yokes with `branch_y=True` and `inline_serifs=True` (feet
replace written kicks). Builders do this when `italic_slant_deg` is set.

**Fallback only:** `serif_bracket` + `soft_union` / `apply_glyph_serifs` when
inventing a letter with no yoke — not the default for n/h/m/u/r.

## Italic (real slanted masters)

**Which parts:**

1. Stem bodies: yoke `branch_y=True` (+ `written_feet` or `inline_serifs`), or
   builders on `ctx.tuned(italic_slant_deg=10)`.
2. Written i/l: `italic_written_stem` / builders.
3. Optional sheet helper: `italic_design(FormSources.from_context(ctx))`.
4. VF pair: `vf_italic_pair(...)` (sets upright `vf_compat_stem_segments` —
   yokes honor `vf_compat_stem`).

```python
from typekernel.parts import DesignContext, GlyphAssembler, n_yoke, build_n
from typekernel.parts.italic import italic_design, vf_italic_pair
from typekernel.parts import FormSources

it_ctx = DesignContext.humanist_sans().tuned(italic_slant_deg=10)
n = build_n(it_ctx)  # branching yoke
# raw:
n2 = GlyphAssembler(it_ctx).add(n_yoke(it_ctx, 0.0, branch_y=True)).build()

# sheet helper / VF:
up, it = vf_italic_pair(FormSources.from_context(DesignContext.humanist_sans()))
```

`oblique_font` is mechanical shear for a `slnt` demo — never ship as Italic.
Do not flip italic-VF construct internals; use `vf_italic_pair` as shipped.

## Open apertures / terminals

**Which parts:** `c_yoke` / `e_yoke` / `s_yoke` or `*_from_o`; knob `aperture` /
`terminal_style`. Real flare: `apply_flare_terminal` or builder `real_flare=True`.

```python
from typekernel.parts import DesignContext, build_o, s_from_o, s_yoke, GlyphAssembler
from typekernel.parts import apply_flare_terminal

ctx = DesignContext.open_print().tuned(aperture=0.7, terminal_style="angled")
s = s_from_o(build_o(ctx), ctx, aperture=ctx.aperture)
# or: GlyphAssembler(ctx).add(s_yoke(ctx, aperture=0.7)).build()
```

## Spacing (agent-chosen)

```python
from typekernel.optics.space import space_font
from typekernel.parts.metrics import auto_class_kern, rhythm_from_control_glyphs

spaced = space_font(drawn, ctx, rhythm=rhythm_from_control_glyphs(drawn["n"], drawn["o"]))
```

## Proof / maintenance CLIs

See [reference.md](reference.md).

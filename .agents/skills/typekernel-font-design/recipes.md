# Recipes (parts only — no aggregate APIs)

All recipes assume Usage A: compose → `Font` → space → compile → proof.
Do **not** reach for `Controls.build_all` / `DesignSequence` / `unlock_*` here.

## Fatten (heavier master)

**Do:** new `DesignContext` with larger `stem`, usually lower relative counters, optional stem relief on letter builders / custom parts. Recompose **every** glyph for that master.

```python
reg = DesignContext.humanist_sans()
bold = reg.tuned(stem=reg.stem * 1.55, aperture=0.5)
# rebuild n/o/... from `bold`, then space_font, then Font — separate master
```

**Do not:** `expand` / stroke inflate a Regular outline and call it Bold.

## Contrast (thick/thin)

```python
ctx = DesignContext.humanist_sans().tuned(contrast=0.72, stress=8.0)
# bowls use stem vs thin; stress rotates the thin axis on rounds
outer, hole = bowl(ctx, 200, 270)  # thickness_v/h follow stem/thin unless overridden
```

Regression notes: `tests/parts/test_stress.py`, `tests/parts/test_knob_coverage.py`.
Round cuts may use internal helpers such as `control._cut` / `_cut_x` when editing letter builders.

## Serif foot / bracketed serif

```python
from typekernel.parts import DesignContext, serif_bracket, vertical_stem
from typekernel.parts.style import Style

ctx = DesignContext.slab_serif()  # or .tuned(style=Style(serif="bracketed"))
stem = vertical_stem(ctx, 80, 0, ctx.x_height)
foot_l = serif_bracket(ctx, x_stem=80 + ctx.stem / 2, y=0, side="left")
foot_r = serif_bracket(ctx, x_stem=80 + ctx.stem / 2, y=0, side="right")
# union into glyph via GlyphAssembler / try_union; or use parts.serifs.apply_glyph_serifs
```

Presets `slab_serif()` / `bracketed_serif()` only seed metrics + `Style.serif`; you still compose.

## Italic (real slanted masters)

```python
from typekernel.parts.italic import italic_design
from typekernel.parts import DesignContext, Controls  # Controls only if calling italic_design helper

# Prefer: compose italic topology yourself, or:
# italic_design(regular_controls_or_context) → italic sheet with construct slant + branching n/h/...
# Then export glyphs per master; do not rename oblique_font output as "Italic".
```

`oblique_font` is mechanical shear for a `slnt` demo — never ship it as Italic.

## Open apertures / terminals

```python
ctx = DesignContext.open_print().tuned(aperture=0.7, terminal_style="angled")
s = s_from_o(build_o(ctx), ctx, aperture=ctx.aperture)
```

## Spacing (agent-chosen)

```python
from typekernel.optics.space import space_font
from typekernel.parts.metrics import auto_class_kern, rhythm_from_control_glyphs

spaced = space_font(drawn, ctx, rhythm=rhythm_from_control_glyphs(drawn["n"], drawn["o"]))
# or set ComposedGlyph.advance yourself, then auto_class_kern(...)
```

## Proof / maintenance CLIs

See [reference.md](reference.md) (`human_review_bundle`, `contact_sheet`, `run_program_exit`, …).

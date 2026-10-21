---
name: typekernel-font-design
description: >-
  Compose installable fonts from typekernel parts (Usage A only). Use when
  building faces, writing examples/*/design scripts, or when the user mentions
  typekernel, DesignContext, parts, Font, or font-as-code in this repo.
---

# typekernel font design (coding agent)

## Product goal

**typekernel is a composable parts toolbox for coding agents.**

You write Python that:

1. picks a `DesignContext` (proportions),
2. **composes glyphs from parts** (or letter builders built from those parts),
3. puts them on a `Font`,
4. spaces them **your way** (sidebearings / kern / `space_font`),
5. compiles and proofs.

Canonical product copy: [docs/AGENT_GOAL.md](../../../docs/AGENT_GOAL.md).

### Only Usage A

```
parts / letter builders → Font.add_chars → space (agent-chosen) → build_font → proof
```

There is **no** blessed aggregate pipeline. Do **not** treat deleted Usage B APIs
(`Controls` / `build_all` / `DesignSequence` / `unlock_*`) or “run the studio/family
example” as the design method. Optional `FormSources.derive` is stock sugar only.

### Companion docs

| File | Content |
| --- | --- |
| [parts-catalog.md](parts-catalog.md) | Stable parts: params, effect, copy-paste calls |
| [recipes.md](recipes.md) | Fatten / contrast / serif foot / italic via **parts** |
| [anti-patterns.md](anti-patterns.md) | Stroke-expand weight, shear-as-italic, dead knobs |
| [reference.md](reference.md) | Maintenance CLIs + acceptance hooks (not design method) |

## Mindset

- A font is a **family of decisions**, expressed in code — not a preset dump.
- Weight = **redesigned masters** (new stem / relief / counters), not stroke expand.
- Italic = **another master set** (`italic_design` / rewritten topology), not shear.
- Proof is part of design. Installable ≠ done.

## Two recipes for the same brief

Brief: *“a slightly wider geometric UI sans Regular, ASCII lowercase first.”*

### Recipe 1 — letter builders (n/o family)

```python
from pathlib import Path

from typekernel.compile import build_font
from typekernel.font import Font
from typekernel.optics.space import space_font
from typekernel.parts import (
    DesignContext,
    a_from_o,
    build_n,
    build_o,
    e_from_o,
    f_from_n,
    h_from_n,
    i_from_n,
    l_from_n,
    m_from_n,
    r_from_n,
    s_from_o,
    t_from_n,
    u_from_n,
)
from typekernel.qa.proof import proof_labeled_waterfall

ctx = DesignContext.geometric_sans().tuned(stem=88.0, x_height=548.0, sidebearing_ratio=0.09)
n, o = build_n(ctx), build_o(ctx)
drawn = {
    "n": n,
    "o": o,
    "h": h_from_n(n, ctx),
    "m": m_from_n(n, ctx),
    "u": u_from_n(n, ctx),
    "r": r_from_n(n, ctx),
    "i": i_from_n(n, ctx),
    "l": l_from_n(n, ctx),
    "f": f_from_n(n, ctx, arm=0.82),
    "t": t_from_n(n, ctx, arm=0.58),
    "a": a_from_o(o, n, ctx),
    "e": e_from_o(o, ctx),
    "s": s_from_o(o, ctx, aperture=0.62),
}
spaced = space_font(drawn, ctx)  # agent-chosen spacing pass
font = Font.from_context(ctx, "Agent Wide UI")
font.add_chars(spaced)
out = build_font(font, Path("out/wide_ui"))
proof_labeled_waterfall([("Regular", out.binaries["otf"])], "nhmuarf tiles", Path("out/wide_ui/proof.png"))
```

### Recipe 2 — raw parts + `GlyphAssembler` (same brief, different construction)

```python
from typekernel.parts import DesignContext, GlyphAssembler, bowl, vertical_stem

ctx = DesignContext.geometric_sans().tuned(stem=88.0, x_height=548.0)
left = vertical_stem(ctx, 40.0, 0.0, ctx.x_height)
outer, hole = bowl(
    ctx,
    cx=220.0,
    cy=ctx.x_height / 2.0,
    rx=150.0,
    ry=ctx.x_height / 2.0 + ctx.overshoot,
)
glyph = (
    GlyphAssembler(ctx)
    .add(left)
    .add(outer)
    .add_hole(hole)
    .union_solids()
    .subtract_holes()
    .build()
)
# Then put glyph in a dict, space_font, Font.add_chars, build_font — same as Recipe 1.
```

Both recipes end the same way: **you** own spacing and compile. Neither calls
deleted `Controls.build_all` / `DesignSequence`.

For full parameter tables see [parts-catalog.md](parts-catalog.md). For fatten /
serif / italic recipes see [recipes.md](recipes.md).

## Definition of done (Usage A)

| Level | Done when |
| --- | --- |
| **Trial** | Named brief + ≥2 different composition approaches considered; glyphs you care about are composed in code; one proof PNG. |
| **One style** | ASCII (or declared charset) composed; spacing chosen; `build_font` succeeds; waterfall / pair proof readable. |
| **Family** | Separate masters per weight (and italic if promised); shared kern groups if VF; proofs per master. |

Human visual sign-off (`approvals/*.json`) is still required for gated voices.
Do **not** flip approval flags unless the user explicitly signs off.

## Workflow checklist

```
- [ ] 1. Brief (use, scripts, weights, italic yes/no, charset)
- [ ] 2. DesignContext preset + documented field deltas
- [ ] 3. Compose control letters (n/o or H/O) from parts / builders
- [ ] 4. Compose remaining letters (builders or PathBuilder / GlyphAssembler)
- [ ] 5. Agent-chosen spacing (`space_font` and/or manual advances + kern)
- [ ] 6. Font names / features matching glyphs you actually added
- [ ] 7. build_font / build_variable_font
- [ ] 8. Proof + fix; commit example script
```

## Maintenance / acceptance (not design)

Program exit and human-review CLIs: [reference.md](reference.md) and
[docs/agent-recipes.md](../../../docs/agent-recipes.md) (ops index).

```bash
pip install -e ".[compile,specimen,boolean]"
PYTHONPATH=src python examples/run_program_exit.py
PYTHONPATH=src python examples/human_review_bundle.py --only appendix-b
PYTHONPATH=src python examples/contact_sheet.py
PYTHONPATH=src python examples/regenerate_outline_hashes.py
PYTHONPATH=src python examples/_legacy/agent_trial/validate_snapshot.py
pytest -q tests/docs/test_development_plan_section8.py
pytest -q tests/parts/test_knob_coverage.py tests/qa/test_style_consistency.py tests/qa/test_originality.py tests/qa/test_multi_voice_exit.py tests/examples/test_zayju_script.py
```

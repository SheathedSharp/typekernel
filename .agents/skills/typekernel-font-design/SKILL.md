---
name: typekernel-font-design
description: >-
  Compose installable fonts from typekernel parts (Usage A only). Use when
  building faces, writing examples/*/design scripts, or when the user mentions
  typekernel, DesignContext, parts, Font, yokes, or font-as-code in this repo.
---

# typekernel font design (coding agent)

## Product goal

**typekernel is a composable parts toolbox + compile exit for coding agents.**

You write Python that:

1. picks a `DesignContext` (proportions / style seeds),
2. **composes glyphs from parts** — prefer **continuous public yokes** for letter
   bodies (`n_yoke`, `h_yoke`, `double_shoulder_yoke`, `u_yoke`, `r_yoke`,
   `bowl_stem_yoke`, `a_yoke`, `c_yoke`, `e_yoke`, `s_yoke`), or letter builders
   that already prefer those yokes,
3. puts them on a `Font`,
4. spaces them **your way** (sidebearings / kern / `space_font`),
5. compiles and proofs.

Canonical product copy: [docs/AGENT_GOAL.md](../../../docs/AGENT_GOAL.md).

### Only Usage A

```
parts / letter builders → Font.add_chars → space (agent-chosen) → build_font → proof
```

There is **no** blessed aggregate pipeline. Do **not** resurrect deleted Usage B
(`Controls` / `build_all` / `DesignSequence` / `unlock_*`) or treat
`examples/_legacy/agent_*` as the design method. Optional `FormSources` /
`italic_design(FormSources…)` is sugar for italic/VF helpers — not the happy path
for inventing letter shapes.

### Default continuous path = yokes

For stem letters (`n`/`h`/`m`/`u`/`r`) and openings (`a`/`c`/`e`/`s`, bowl+stem
`b`/`d`/`p`/`q`), draw **one continuous contour** (or the documented outer+hole
pair) with a public yoke instead of kit-of-parts `vertical_stem` + `shoulder` +
boolean union. Letter builders (`build_n`, `m_from_n`, `a_from_o`, …) already
prefer yokes on the Usage A path (including italic, slab/bracket, and
`vf_compat_stem_segments`).

Use kit-of-parts + `soft_union` only when no yoke covers the shape yet, or when
you are deliberately inventing a new topology.

### Companion docs

| File | Content |
| --- | --- |
| [parts-catalog.md](parts-catalog.md) | Stable parts: every param has name+unit, bigger/smaller, affected glyphs, range/breakage, copy-paste |
| [recipes.md](recipes.md) | Fatten / contrast / serif foot / italic via **which parts** |
| [anti-patterns.md](anti-patterns.md) | Stroke-expand, shear-as-italic, dead knobs, kit-of-parts when a yoke exists |
| [reference.md](reference.md) | Maintenance CLIs (not design method) |

## Mindset

- A font is a **family of decisions**, expressed in code — not a preset dump.
- Weight = **redesigned masters** (new stem / relief / counters), not stroke expand.
- Italic = **another master set** (`italic_design` / yoke `branch_y` / written
  kicks), not mechanical shear.
- Proof is part of design. Installable ≠ done.
- **Smoke green ≠ ship.** Pytest / `examples/skill_validate` check build, export, packing, VF segment invariants. Visual accept is a **vision agent** reading proof PNGs (`examples/skill_validate/VISUAL_ACCEPT.md`). Do not reintroduce hairline / white-gap / width-delta “quality PASS” gates in code.

## Two recipes for the same brief

Brief: *“a slightly wider geometric UI sans Regular, ASCII lowercase first.”*

You must consider **≥2 different composition recipes** for the same brief
(builders-via-yokes vs raw yokes, or yokes vs intentional kit-of-parts for a
letter the yoke does not cover). Do not ship the first recipe that compiles.

### Recipe 1 — letter builders (prefer yokes under the hood)

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
n, o = build_n(ctx), build_o(ctx)  # continuous yokes on Usage A
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
spaced = space_font(drawn, ctx)
font = Font.from_context(ctx, "Agent Wide UI")
font.add_chars(spaced)
out = build_font(font, Path("out/wide_ui"))
proof_labeled_waterfall([("Regular", out.binaries["otf"])], "nhmuarf tiles", Path("out/wide_ui/proof.png"))
```

### Recipe 2 — raw public yokes + `GlyphAssembler` (same brief)

```python
from typekernel.parts import (
    DesignContext,
    GlyphAssembler,
    double_shoulder_yoke,
    e_yoke,
    n_yoke,
    r_yoke,
    s_yoke,
    u_yoke,
)

ctx = DesignContext.geometric_sans().tuned(stem=88.0, x_height=548.0)
drawn = {
    "n": GlyphAssembler(ctx).add(
        n_yoke(ctx, 0.0, counter=ctx.x_height * 0.44, stem_width=ctx.stem)
    ).build(),
    "m": GlyphAssembler(ctx).add(
        double_shoulder_yoke(ctx, 0.0, counter=ctx.x_height * 0.44, stem_width=ctx.stem)
    ).build(),
    "u": GlyphAssembler(ctx).add(
        u_yoke(ctx, 0.0, counter=ctx.x_height * 0.44, stem_width=ctx.stem)
    ).build(),
    "r": GlyphAssembler(ctx).add(
        r_yoke(ctx, 0.0, arm=0.55, counter=ctx.x_height * 0.44, stem_width=ctx.stem)
    ).build(),
    "e": GlyphAssembler(ctx).add(e_yoke(ctx, aperture=0.62)).build(),
    "s": GlyphAssembler(ctx).add(s_yoke(ctx, aperture=0.62)).build(),
}
# Then space_font → Font.add_chars → build_font — same exit as Recipe 1.
```

Italic variant of Recipe 2: pass `branch_y=True` (and `inline_serifs=True` for
slab/bracket) on stem yokes, or set `ctx = ctx.tuned(italic_slant_deg=10)` and
use builders / `italic_design`. Do **not** shear an upright font and label it Italic.

Both recipes end the same way: **you** own spacing and compile.

Parameter tables: [parts-catalog.md](parts-catalog.md). Fatten / serif / italic:
[recipes.md](recipes.md).

## Definition of done (Usage A)

| Level | Done when |
| --- | --- |
| **Trial** | Named brief + ≥2 different composition approaches considered; glyphs you care about are composed in code (yokes preferred); one proof PNG. |
| **One style** | ASCII (or declared charset) composed; spacing chosen; `build_font` succeeds; waterfall / pair proof readable. |
| **Family** | Separate masters per weight (and italic if promised); shared kern groups if VF; proofs per master. |

Human visual sign-off (`approvals/*.json`) is still required for gated voices.
Do **not** flip approval flags unless the user explicitly signs off.

## Workflow checklist

```
- [ ] 1. Brief (use, scripts, weights, italic yes/no, charset)
- [ ] 2. DesignContext preset + documented field deltas
- [ ] 3. Compose control letters with yokes / builders that prefer yokes
- [ ] 4. Compose remaining letters (yokes first; kit-of-parts only if needed)
- [ ] 5. Agent-chosen spacing (`space_font` and/or manual advances + kern)
- [ ] 6. Font names / features matching glyphs you actually added
- [ ] 7. build_font / build_variable_font
- [ ] 8. Proof + fix; commit example script
```

## Maintenance / acceptance (not design)

Program exit and human-review CLIs: [reference.md](reference.md) and
[docs/agent-recipes.md](../../../docs/agent-recipes.md) (ops index).
This is **not** the design method — design stays Usage A + yokes above.

```bash
pip install -e ".[compile,specimen,boolean]"
PYTHONPATH=src python examples/run_program_exit.py
PYTHONPATH=src python examples/human_review_bundle.py --only appendix-b
PYTHONPATH=src python examples/contact_sheet.py
PYTHONPATH=src python examples/regenerate_outline_hashes.py
PYTHONPATH=src python examples/_legacy/agent_trial/validate_snapshot.py
pytest -q tests/docs/test_development_plan_section8.py
pytest -q tests/parts/test_builders_prefer_yokes.py tests/parts/test_opening_yokes.py
pytest -q tests/parts/test_knob_coverage.py tests/qa/test_style_consistency.py tests/qa/test_originality.py tests/qa/test_multi_voice_exit.py tests/examples/test_zayju_script.py
```

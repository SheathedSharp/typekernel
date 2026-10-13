# Agent catalog — typekernel (Controls-first)

**Production path for coding agents**: `DesignContext` → `Controls.build_all()` →
`space_font` → `compose_font_from_controls()` → `build_font`. Full workflow:
[`.agents/skills/typekernel-font-design/SKILL.md`](../../.agents/skills/typekernel-font-design/SKILL.md).

Legacy `parts.latin` / `parts.skeleton_recipes` remain for demos but are **not**
re-exported from `typekernel.parts`.

```bash
pip install -e ".[dev,compile,specimen,boolean]"
```

Preview a few glyphs: `python examples/agent_glyph_preview/build_preview.py`

## Controls (family control sheet)

| API | One-liner |
| --- | --- |
| `Controls.from_context(ctx)` | Control records for `n` / `o` (+ derived caps). |
| `controls.tuned_n(counter=…)` / `tuned_o(rx=…)` | Tune one control; `build_all()` refreshes the family. |
| `controls.with_stem_relief()` | Heavy-master counter relief (designed delta). |
| `controls.with_glyph("f", builder)` | Replace one letter’s derivation (single-glyph master). |
| `controls.build_all(chars=None)` | Draw lowercase / caps / figures / punctuation. |
| `RELATED_FORMS`, `CAP_FORMS`, `PUNCT_FORMS` | Derivation maps (see `parts.family`). |

## Compile (agent-safe assembly)

| API | One-liner |
| --- | --- |
| `compose_font_from_controls(controls, family, style, options=…)` | Spacing + kern + **feature-safe** OpenType text. |
| `FamilyBuildOptions(liga=, tnum=, case=)` | Only enable features whose glyphs you add. |
| `reference_kern_classes(controls)` | Shared kern groups for VF masters. |
| `build_font(font, out_dir)` | UFO → OTF/TTF. |
| `build_variable_font(masters, out_dir)` | Designed masters → VF. |

## QA

| API | One-liner |
| --- | --- |
| `qa.sentence_gate.check_sentence_gate(controls)` | Agent sentence regression on **Controls** pipeline. |
| `qa.proof.proof_context(otf, text, out.png)` | Proof from compiled binary. |
| `qa.score.zayju_report(ctx)` | Legacy **latin** zayju benchmark (optical spacing). |

## DesignContext (scene parameters)

| Constructor | One-liner |
| --- | --- |
| `DesignContext(...)` | Frozen family rhythm: stem, contrast, overshoot, roundness, tracking, aperture, … |
| `DesignContext.code_clear()` | Default coding sans preset. |
| `DesignContext.geometric_sans()` | Neo-grotesque preset. |
| `DesignContext.humanist_sans()` | More contrast, open aperture. |
| `DesignContext.mono()` | Heavier stems, zero tracking. |
| `DesignContext.display()` | Thinner stems, loose tracking. |
| `ctx.tuned(**fields)` | Copy with selected knobs overridden. |

## Primitives, transforms, boolean

See sections below in git history or `typekernel.parts` submodule docs (`primitives`,
`transforms`, `compose`, `pen`). Prefer deriving letters via `Controls` before
hand-assembling with `GlyphAssembler`.

## Legacy (demos only — import submodules)

| Module | Use |
| --- | --- |
| `typekernel.parts.latin` | Old per-letter recipes; `word_zayju()` for zayju optical tests. |
| `typekernel.parts.skeleton_recipes` | `skel_*` shims to control glyphs. |

## Minimal agent sketch

```python
from typekernel.compile import FamilyBuildOptions, build_font, compose_font_from_controls
from typekernel.parts import Controls, DesignContext

ctx = DesignContext.code_clear()
controls = Controls.from_context(ctx).tuned_n(counter=controls.n.counter * 1.05)
font = compose_font_from_controls(
    controls,
    "My Family",
    options=FamilyBuildOptions(liga=True),
)
build_font(font, "out/")
```

## Honest gaps

- One sans topology from `n`/`o`; script/serif need new parts or UFO import.
- `f`/`t` etc. are derived — use `with_glyph()` or fix builders when proof fails.
- Sentence gate thresholds are **regression** bars, not “beautiful” certification.
- No TrueType hinting; OpenType beyond basic `liga`/`tnum`/`case` is partial.

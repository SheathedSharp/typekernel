---
name: typekernel-font-design
description: >-
  Design and build complete font families with typekernel the way a human type
  designer would—proportions, control glyphs, weights, punctuation, OpenType,
  spacing, proof. Use when creating fonts, adding masters, extending glyph sets,
  writing examples/* build scripts, or when the user mentions typekernel,
  DesignContext, Controls, or font-as-code in this repo.
---

# typekernel font design (coding agent)

## Product goal

**typekernel 的定位应该是让 coding agent 通过使用这个基础库，像人类字体设计时一样去创建一种字体「包括各个字重，符号等等」。**

Canonical copy: [docs/AGENT_GOAL.md](../../../docs/AGENT_GOAL.md)

## Mindset

Think **family**, not **single glyph**. One codepoint is done only with sidebearings, neighbors, and sentence proof—not an isolated outline.

Do **not** simulate weight with stroke expand, script with oblique shear, or OpenType features without the referenced glyphs.

## Definition of done

`check_sentence_gate` is a **regression brake**, not a design award. Pick a level before editing. Stopping at a lower level when the brief asks for a family is a failed delivery.

| Level | Where | Done when |
| --- | --- | --- |
| **L0 trial** | `examples/agent_studio/` | Named preset + **one documented delta** from that preset's fields + `tuned_glyph` / `with_glyph` on **≥2** of `f t j a s e`. Gate text is `AGENT_SENTENCE` only. `design_review(..., baseline=Controls.from_context(preset))` shows optical gap ratio and non-terminal G1 **not worse** than that preset. |
| **L1 one style** | still one weight | L0, and the fixed pairs `Ta To fi fl rn 011` have **no silhouette collision** (`min optical gap > 0`). |
| **L2 family** | `examples/agent_family/` or `examples/<family>/build_*.py` | Regular + Light and Bold (or a VF) as **separate** `Controls` masters. Bold uses `with_stem_relief()`. `compose_font_from_controls` + `reference_kern_classes` shared across masters. |

The pair check is inside `check_sentence_gate`, so L0's build already runs it. L1 is the bar for calling that single style readable. L2 is the bar for "a family".

### Anti-patterns (these are not done)

- Editing the proof sentence, or passing the brief sentence into `check_sentence_gate`, until the gate prints ok.
- Declaring success from `sentence gate ok` plus a PNG.
- Untethered floats (`stem=78`, `x_height=520`) with no preset field to compare. Tune **one field** as a delta from the preset (its `sidebearing_ratio` is `0.10`; `0.11` is a decision). Stay near the preset on a Regular voice — large stem jumps belong on a **new master**, and they must not worsen that master's own baseline.
- One `with_glyph("f", ...)` and a `tuned_n` / `tuned_o` scale (`* 1.03`) treated as a new design.
- Shipping Light/Bold by editing only `agent_studio/design.py`.
- Naming oblique shear, `lean`, or tracking as italic or as copperplate / connected script.

### Unsupported voices

Copperplate and connected script need a **new topology** in `parts`, or a UFO import with typekernel doing spacing and features. Say so. Do not fake the voice.

Recipes (patch shapes, when to leave `Controls` for a `PathBuilder`): [`docs/agent-recipes.md`](../../../docs/agent-recipes.md).

## Designer-order workflow

Copy and track:

```
- [ ] 0. Level: L0 trial / L1 one style / L2 family (see Definition of done)
- [ ] 1. Brief (use, scripts, weights, italic yes/no, symbol set)
- [ ] 2. DesignContext (named preset + documented deltas, not free floats)
- [ ] 3. Control glyphs n/o (+ H/O for caps/figures) — inspect outlines, then edit
- [ ] 4. Derive charset via Controls.build_all(subset or supported)
- [ ] 5. Fix ≥2 weak letters (f,t,j,a,s,e) with with_glyph or a dedicated builder
- [ ] 6. space_font + auto_class_kern (shared kern classes for VF)
- [ ] 7. Font: names, space_width, features matching actual glyphs
- [ ] 8. build_font / build_variable_font (L2: one master per weight)
- [ ] 9. design_review + locked AGENT_SENTENCE gate; brief sentence is a second specimen
- [ ] 10. pytest if touching library; example script committed
```

### Step details

**1 — Brief**  
Record: family name, target style (geometric sans / humanist / mono / …), axes (wght, wdth, ital), minimum charset (ASCII, Latin-1, punctuation), tabular nums, ligatures.

**2 — DesignContext**  
Start from a preset: `code_clear()`, `humanist_sans()`, `geometric_sans()`, `display()`, `paper_ink()`, `mono()`. Override with `.tuned(...)` as a **documented delta from that preset's fields** (read the preset, then change one knob). One context per **voice**; do not mix voices in one master set. A new weight is a new master, not a bigger `stem` on the Regular sheet you are comparing to the preset.

**3 — Controls**  
`Controls.from_context(ctx)`. Tune with `tuned_n`, `tuned_o`, `tuned_cap_h`, `tuned_cap_o`. Weak letters: `.tuned_glyph("f", arm=0.82)` (see `parts/glyph_specs.py`; caps include `A`/`E`/`F`/`G`/`K`/`L`/`R`/`T`/`Y`/`V`/`W`/`X`/`Z`/`M`/`N` specs). Heavy masters: `.with_stem_relief()` on that master’s sheet only.

**4 — Build glyphs**  
`drawn = controls.build_all()` or explicit substring. Extended Latin / composites: `add_composite_latin` after spacing (see `examples/first_font/build_font.py`).  
`compose_font_from_controls` runs **join polish** (`tangent_fix`) on every outline before spacing; disable with `FamilyBuildOptions(joins_policy="noop")` for VF debugging.

**5 — Spacing & kerning**  
```python
rhythm = rhythm_from_control_glyphs(drawn["n"], drawn["o"])
spaced = space_font(drawn, ctx, rhythm=rhythm)
classes = auto_side_kern_classes(spaced, ctx)
kern = auto_class_kern(spaced, classes, target=rhythm)
```

**VF**: compute `kern_classes` once from the **regular** spaced set; reuse for every master (`examples/italic_family/build_italic_vf.py`).

**6 — Font + features (prefer helper)**  
```python
from typekernel.compile import FamilyBuildOptions, compose_font_from_controls, build_font

font = compose_font_from_controls(
    controls,
    "My Family",
    options=FamilyBuildOptions(liga=True),  # only liga — no ghost .tf/.case refs
)
build_font(font, out_dir, formats=("otf", "ttf"))
```

Single-glyph master: `controls.tuned_glyph("f", arm=0.9)` or `with_glyph(...)` for custom topology.

**7 — Variable fonts**  
```python
from typekernel.compile import build_variable_font, reference_kern_classes
classes = reference_kern_classes(regular_controls)
# reuse classes for every Master font
```

Extras: `pip install -e ".[compile,specimen,boolean]"` (boolean optional).

**8 — Proof + sentence gate**  
```python
from typekernel.parts import Controls, DesignContext
from typekernel.qa.design_review import design_review
from typekernel.qa.proof import proof_context
from typekernel.qa.sentence_gate import AGENT_SENTENCE, check_sentence_gate

baseline = Controls.from_context(DesignContext.humanist_sans())  # the preset you started from
review = design_review(controls, baseline=baseline)
# review.failures, review.l0_gaps, and review.charset_failures must all be empty.
# charset_failures = full supported charset lint + identity (family_gate).
# Do not pass the brief sentence here — it cannot make the gate pass.
_report, failures = check_sentence_gate(controls, baseline=baseline)

proof_context(otf_path, AGENT_SENTENCE, out_png, size=32)  # pass/fail specimen
proof_context(otf_path, brief_sentence, brief_png, size=32)  # second specimen only
```

Read `review.summary()`: optical-ratio / G1 deltas, worst pair, weak-glyph overrides. Then edit the design. Empty `failures` means the regression brake held, not that the family is finished.

Use the locked sentence and the brief sentence at **body** size (24–36 px), `features=["kern","liga"]` when enabled.

## Agent studio (L0) and agent family (L2)

**Do not** treat the repo as “run one script → finished font.” The agent **writes** the design in Python, then exports proofs.

**L0 trial** — edit **`examples/agent_studio/design.py`**, run **`python examples/agent_studio/build.py`**. One Regular voice. The gate scores `AGENT_SENTENCE`; `BRIEF_SENTENCE` is `sentence_brief.png` only. A failing review (sentence, L0 gaps, or **charset / family_gate**) exits non-zero. Built-in presets pass charset gate; agent deltas must keep it green. Read `out/review/` (deltas, worst pair, control PNGs) before a second pass.

M5 trial metrics: `typekernel.qa.trial_protocol.snapshot_trial` + `examples/agent_trial/snapshot_presets.py` (see `docs/AGENT_TRIALS.md`).

**L2 family** — copy **`examples/agent_family/`** to `examples/<family>/`. Implement `design_controls` / `design_light` / `design_bold` (or VF masters) and `build_family.py` (`compose_font_from_controls`, shared kern classes). Do not deliver Light/Bold inside `agent_studio`.

Proof helper (requires **your** `Controls`):

```python
from typekernel.qa.agent_preview import build_glyph_preview
from typekernel.qa.sentence_gate import AGENT_SENTENCE

paths = build_glyph_preview(
    controls,
    family="My Trial",
    focus="n o a f t",
    sentence=AGENT_SENTENCE,  # locked pass/fail specimen
    out_dir="out/preview",
)
# paths["grid"], paths["sentence"], paths["otf"]
# Brief sentence: proof_context(paths["otf"], brief, "sentence_brief.png") — not the gate.
```

Show the user **`grid.png`**, **`sentence.png`**, and the review summary (deltas, worst pair, which weak glyphs you overrode). Requires **boolean** for best `f`/`t` crossbars.

## Weights & variable fonts

- **Static family**: one `Controls` + one `build_font` per weight/style file.
- **VF**: each location is a full redrawn `Font` inside `Master({axis: value}, font)`. Minimum masters so **each axis** min ≠ max (`check_masters`).
- Italic axis: `italic_design(regular)` (construct slant + counter lean; `italic_controls` is a deprecated alias). Branching `n/h/r/u/m` and italic `f` descender ship with M4; use `vf_upright_controls` for upright VF masters. Do **not** use `oblique_font` / `ObliqueTransform` for `ital=1` style names.

## Symbols & charset

Default punctuation/figures live in `Controls.supported` via `PUNCT_FORMS`, caps, figures. Opt-in extended Latin through `build_all` + diacritic helpers. If a symbol overlaps at extreme stems, fix topology in `parts/punctuation.py`—do not hide missing glyphs.

## When the library is not enough

| User ask | Wrong approach | Right approach |
| --- | --- | --- |
| Copperplate / connected script | Crank `lean`, oblique, tracking | Say the topology is missing; add it in `parts` or import UFO and let typekernel space / feature it |
| One ugly letter | Global context only | `with_glyph` or a dedicated builder; re-read `design_review` glyphs |
| “Make it bolder” | Scale outline or raise `stem` on the Regular sheet | New master: higher `stem` + `with_stem_relief()` |
| Gate fails on the brief sentence | Shorten or swap the proof string | Keep `AGENT_SENTENCE` as the only pass/fail text; fix spacing, joins, or the weak glyph |

## Reference examples

| Example | Teaches |
| --- | --- |
| `examples/agent_studio/` | **L0 trial** — `design.py` + locked gate + `design_review` |
| `examples/agent_family/` | **L2 template** — Regular / Light / Bold, shared kern, TODOs for italic and extended Latin |
| `examples/first_font/` | Full static family pipeline + features |
| `examples/zayju_letter/` | Hand-built `n` with `PathBuilder` when `Controls` is not enough |
| `examples/variable_family/` | wght VF, designed counters |
| `examples/italic_family/` | wght × ital, shared kern classes |
| `examples/variable_width/build_vfwd.py` | wght × wdth |
| `examples/oblique_font/` | slnt via shear only |

## Maintenance (for agents editing the repo)

When changing default build order, `standard_feature_text`, master checks, or presets:

1. Update this `SKILL.md` (and [reference.md](reference.md) if API paths moved).
2. Update [docs/AGENT_GOAL.md](../../../docs/AGENT_GOAL.md) if the product goal shifts.
3. Add or adjust an `examples/*` script that demonstrates the new convention.

## More detail

- Module map & pitfalls: [reference.md](reference.md)
- Human-facing vision: [docs/VISION.md](../../../docs/VISION.md)

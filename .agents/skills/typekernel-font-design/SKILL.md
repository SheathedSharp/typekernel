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

## Designer-order workflow

Copy and track:

```
- [ ] 1. Brief (use, scripts, weights, italic yes/no, symbol set)
- [ ] 2. DesignContext (preset + documented tuned fields)
- [ ] 3. Control glyphs n/o (+ H/O for caps/figures) — inspect outlines
- [ ] 4. Derive charset via Controls.build_all(subset or supported)
- [ ] 5. Fix weak derived letters (f,t,s,…) — tune metrics or add dedicated builder in parts
- [ ] 6. space_font + auto_class_kern (shared kern classes for VF)
- [ ] 7. Font: names, space_width, features matching actual glyphs
- [ ] 8. build_font / build_variable_font
- [ ] 9. qa.proof on compiled binary with brief sentence(s)
- [ ] 10. pytest if touching library; example script committed
```

### Step details

**1 — Brief**  
Record: family name, target style (geometric sans / humanist / mono / …), axes (wght, wdth, ital), minimum charset (ASCII, Latin-1, punctuation), tabular nums, ligatures.

**2 — DesignContext**  
Start from a preset: `code_clear()`, `humanist_sans()`, `geometric_sans()`, `display()`, `paper_ink()`, `mono()`. Override with `.tuned(stem=…, contrast=…, …)` or `replace(..., terminal_style="angled")`. One context per **voice**; do not mix voices in one master set.

**3 — Controls**  
`Controls.from_context(ctx)`. Tune with `tuned_n`, `tuned_o`, `tuned_cap_h`, `tuned_cap_o`. Heavy masters: `.with_stem_relief()` on that master’s sheet only.

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

Single-glyph master: `controls.with_glyph("f", lambda n, o, c: f_from_n(n, c, arm=0.9))`.

**7 — Variable fonts**  
```python
from typekernel.compile import build_variable_font, reference_kern_classes
classes = reference_kern_classes(regular_controls)
# reuse classes for every Master font
```

Extras: `pip install -e ".[compile,specimen,boolean]"` (boolean optional).

**8 — Proof + sentence gate**  
```python
from typekernel.qa.proof import proof_context
from typekernel.qa.sentence_gate import check_sentence_gate

proof_context(otf_path, "Your sentence here.", out_png, size=32)
_failures = check_sentence_gate(controls)[1]  # regression on Controls pipeline
```

Use the user’s sentence at **body** size (24–36 px), `features=["kern","liga"]` when enabled.

## Weights & variable fonts

- **Static family**: one `Controls` + one `build_font` per weight/style file.
- **VF**: each location is a full redrawn `Font` inside `Master({axis: value}, font)`. Minimum masters so **each axis** min ≠ max (`check_masters`).
- Italic axis: `italic_controls(regular_sheet)` per italic master; do not use `ObliqueTransform` for `ital=1`.

## Symbols & charset

Default punctuation/figures live in `Controls.supported` via `PUNCT_FORMS`, caps, figures. Opt-in extended Latin through `build_all` + diacritic helpers. If a symbol overlaps at extreme stems, fix topology in `parts/punctuation.py`—do not hide missing glyphs.

## When the library is not enough

| User ask | Wrong approach | Right approach |
| --- | --- | --- |
| Copperplate / connected script | Crank `lean`, oblique, tracking | Say voice unsupported; add new glyph topology in `parts` or import UFO |
| One ugly letter | Global context only | Tune control metrics; or dedicated `*_from_n` / cap builder; sentence proof |
| “Make it bolder” | Scale outline | New master: higher `stem` + relief |

## Reference examples

| Example | Teaches |
| --- | --- |
| `examples/first_font/` | Full static family pipeline + features |
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

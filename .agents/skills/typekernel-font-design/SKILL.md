---
name: typekernel-font-design
description: >-
  Design fonts with typekernel via Project / System / draw / plugins (ARCHITECTURE.md §4).
  Use when scaffolding with tk new, editing starters/latin_sans, writing glyphs with @glyph,
  running tk proof / tk audit / tk build, or when the user mentions typekernel font-as-code.
---

# typekernel font design (coding agent)

**This is the active workflow** ([docs/ARCHITECTURE.md](../../../docs/ARCHITECTURE.md) §4).

Letter geometry lives in the **project** (starter). The kernel has no letter builders.
Do **not** import `typekernel.parts` or `DesignContext` — they were removed in M4.

## Product goal

Write a font project that:

1. declares proportions in `system.py` (`System` / zones / stems / tokens),
2. draws glyphs with `typekernel.draw` (`Writer` / fragments / named nodes / overlap),
3. registers them with `@glyph` under `glyphs/`,
4. configures corners/ends plugins in `font.py`,
5. spaces via `spacing.py` (metrics keys + kern),
6. audits, proofs, and compiles (`tk audit` / `tk proof` / `tk build`).

Canonical product copy: [docs/AGENT_GOAL.md](../../../docs/AGENT_GOAL.md).

## §4 workflow (follow in order)

```
tk new myfont --starter latin-sans
1. brief.md                         # intent in prose
2. system.py                        # every number needs a reason
3. control glyphs n o H O           → tk proof control  → look, change, repeat
4. elements.py + expand groups      → tk proof lc.n / lc.o / diag / …
5. tk audit                         → stem / zone / direction / compat; fix in glyph code
6. corners / ends in font.py        → tk proof all
7. spacing.py                       → tk proof spacing / kern
8. masters (Light/Bold) / italic    → tk audit --compat; tk proof ladder; tk build --variable
9. tk build                         → OTF / TTF / VF
```

Default starter: **latin-sans** (full Latin + figures + punct + spacing + Light/Bold).

## Hard rules

- **Change fragments / elements** when a join looks wrong. Never add heal / blend / seal passes.
- Put letter geometry only in the project (`elements.py`, `glyphs/**`). Kernel packages stay letter-free.
- Prefer **overlap construction** (stem + trough) over boolean unions for interpolatable masters.
- Name nodes (`stem.l`, `arch.…`) so `tk audit` can measure them.
- Advances / LSB / RSB: declare metrics keys in `spacing.py`; do not rely on bbox-only advances.
- Conventional commits; local review against ARCHITECTURE.md §9 / §9.11 after each commit.

## Companion docs

| File | Content |
| --- | --- |
| [reference.md](reference.md) | CLI, System, @glyph, plugins cheat-sheet |
| [recipes.md](recipes.md) | Common edits: heavier stems, tighter spacing, corner plugins |
| [anti-patterns.md](anti-patterns.md) | Stroke-expand weight, heal/blend/seal, resurrecting parts |

Elements live **in the project**, not in a library catalog. Copy patterns from
`src/typekernel/starters/latin_sans/elements.py` and sibling glyph files.

## Minimal loop

```bash
pip install -e ".[compile,specimen]"
tk new trial --starter latin-sans
cd trial
# edit system.py tokens / stem
tk build .
tk proof control .
tk audit .
```

Python equivalent: `examples/latin_sans_quickstart/build.py`.

---
name: typekernel-font-design
description: >-
  Design fonts with typekernel via Project / System / draw / plugins (ARCHITECTURE.md「标准工作流」).
  Use when scaffolding with tk new, editing starters/latin_sans, writing glyphs with @glyph,
  running tk proof / tk audit / tk build, or when the user mentions typekernel font-as-code.
---

# typekernel font design (coding agent)

**This is the active workflow** ([docs/ARCHITECTURE.md](../../../docs/ARCHITECTURE.md) 标准工作流).

Letter geometry lives in the **project** (starter). The kernel packages contain no
letter builders — do not go looking for one there.

> **Starter quality:** 结构示例，字形未通过视觉评审，不要当作字形质量范本。
> Copy structure from `latin-sans` / `latin-humanist-italic` / `latin-chancery`; do not treat their outlines as a visual target.

## Product goal

Write a font project that:

1. declares proportions in `system.py` (`System` / zones / stems / tokens),
2. draws glyphs with `typekernel.draw` (`Writer` / fragments / named nodes / overlap),
3. registers them with `@glyph` under `glyphs/`,
4. configures corners/ends plugins in `project.py` (`PROJECT`),
5. spaces via `Project.metrics` / `spacing.py` (`METRICS` + `KERNING`),
6. audits, proofs, and compiles (`tk audit` / `tk proof` / `tk build`).

## 标准工作流（按顺序执行）

```
tk new myfont --starter latin-sans
1. brief.md + system.py BRIEF/INTENT # prose + typed Intent (see reference.md)
2. system.py numbers                 # must stay inside Intent bands; tk audit checks
3. control glyphs n o H O           → tk proof control  → look, change, repeat
4. elements.py + expand groups      → tk proof --glyph n / --text "…"
5. tk audit                         → stem / zone / direction / compat; fix in glyph code
6. corners / ends in project.py     → tk proof all
7. spacing.py                       → tk proof spacing / kern
8. masters (Light/Bold) / italic    → tk audit --compat; tk proof ladder; tk build --variable
9. tk build                         → OTF / TTF / VF
```

Default starter: **latin-sans** (full Latin + figures + punct + spacing + Light/Bold). 结构示例，字形未通过视觉评审，不要当作字形质量范本。
Also: **latin-humanist-italic** (skeleton+pen, `System.slant`), **latin-chancery**
(minimal + `pen_dot` / flourish helpers — do not reinvent curls).

## See before you ship (perception)

Designers' loop is driven by **looking**. Do not invent private PIL croppers:

| Need | Command |
| --- | --- |
| Arbitrary string | `tk proof --text "the quick brown fox"` |
| Zoom one character | `tk proof --glyph n` (or `tk proof --glyph æ`) |
| Control / spacing / kern / charset | `tk proof control` / `spacing` / `kern` / `charset` |
| Weight ladder (VF if present) | `tk proof ladder` |
| Pen contrast×angle preview | `tk pen --contrast 0.26 --angle 30` |
| Even-odd cavity hunt (opt-in) | `tk audit --overlap` |
| Static ship without overlap cavities | `tk build --resolve-overlaps` (not with `--variable`) |
| Intent vs System drift | `tk audit` (`BRIEF`/`INTENT` in system.py → `[warn] intent`) |

## Hard rules

- **Change fragments / elements** when a join looks wrong. Never add heal / blend / seal passes.
- Put letter geometry only in the project (`elements.py`, `glyphs/**`). Kernel packages stay letter-free.
- Prefer **overlap construction** (stem + trough) over boolean unions for interpolatable masters.
- Name nodes (`stem.l`, `arch.…`) so `tk audit` can measure them.
- Advances / LSB / RSB: declare `METRICS` keys in `spacing.py` (wired on `PROJECT.metrics`); do not rely on bbox-only advances or `<glyph>_advance` tokens.
- Conventional commits; local review against ARCHITECTURE.md 交接规格 / 设计禁令与边界 after each commit.

## Constructors & optics (do not rediscover)

Read **[reference.md](reference.md)** before hand-rolling primitives. Especially:

- `typekernel.draw.construct`: `hook`, `tensioned_arc`, `spring`, `diagonal_band`, `superellipse_quarter`
- `typekernel.plugins.construct.skeleton_pen`: `broad_nib`, `pointed_pen`, `expand_skeleton`
- `typekernel.optics.stem`: `measure_oriented_stem`, `diagonal_compensation`, `vertical_equiv_from_diagonal`

Cold-start agents: open `reference.md` in the same pass as this skill, then follow [trials.md](trials.md) (cold-start / final-acceptance checklist).

## Companion docs

| File | Content |
| --- | --- |
| [reference.md](reference.md) | CLI, System, construct, optics, @glyph, plugins |
| [recipes.md](recipes.md) | Common edits: heavier stems, tighter spacing, corner plugins |
| [anti-patterns.md](anti-patterns.md) | Stroke-expand weight, heal/blend/seal, self_union policy |
| [trials.md](trials.md) | Cold-start / final-acceptance checklist (tracked) |

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
tk proof --text "hamburgefonstiv" .
tk proof --glyph n .
tk audit .
```

Python equivalent: `examples/latin_sans_quickstart/build.py`.

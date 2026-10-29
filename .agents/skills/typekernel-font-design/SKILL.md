---
name: typekernel-font-design
description: >-
  Design fonts with typekernel via Project / System / draw / plugins (ARCHITECTURE.md「标准工作流」).
  Use when scaffolding with tk new, editing starters/latin_sans, writing glyphs with @glyph,
  running tk see / tk explain / tk proof / tk audit / tk review / tk build, or when the user
  mentions typekernel font-as-code.
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
3. registers them with `@glyph` under `glyphs/` (and `expect.py` topology/reach tables),
4. configures corners/ends plugins in `project.py` (`PROJECT`),
5. spaces via `Project.metrics` / `spacing.py` (`METRICS` + `KERNING`),
6. **sees**, audits, reviews, proofs, and compiles.

## 主循环（perception-first）

```
tk new myfont --starter latin-sans
1. brief.md + system.py BRIEF/INTENT
2. system.py numbers (inside Intent bands)
3. For each control glyph / group:
     tk see <glyph> --context [--masters]
     tk explain <glyph> --json
     edit glyph / elements / system
     tk audit
     tk see <glyph> --diff
     tk review record <group> --verdict pass|fail --note "…"
4. tk status                         # task board; groups start unreviewed
5. corners / ends → tk proof all
6. spacing → tk proof spacing / kern
7. masters → tk audit --masters all; tk proof ladder; tk build --variable
8. tk build
```

Do **not** skip `tk see` / `tk explain` and guess from compile errors alone.

## See / explain / status

| Need | Command |
| --- | --- |
| Edit view + JSON sidecar | `tk see n` |
| Context + masters | `tk see n --context --masters` |
| Before/after | `tk see n --diff` |
| Structured measures | `tk explain n --json` |
| Task board | `tk status` |
| Group review | `tk review open lc.n` / `tk review record lc.n --verdict pass --note "…"` |
| Arbitrary string | `tk proof --text "…"` |
| Zoom one character | `tk proof --glyph n` |
| Small-px waterfall / gray | included in `tk proof all` |
| Features (needs uharfbuzz) | `tk proof --features smcp --text "…"` |
| Pen preview | `tk pen --contrast 0.26 --angle 30` |
| Diagnostics JSON | `tk audit --json` / `--masters all` / `--strict` |

## Hard rules

- **Change fragments / elements** when a join looks wrong. Never add heal / blend / seal passes.
- Put letter geometry only in the project. Kernel packages stay letter-free.
- Prefer **overlap construction** over boolean unions for interpolatable masters.
- Name nodes so `tk audit` / `tk explain` can measure them.
- Advances via `METRICS` keys — not bbox-only advances or `<glyph>_advance` tokens.
- **Do not** edit `expect.py` just to silence findings; justify every expect change in the review note.
- **Do not** write `approved: true` as an agent; human approvals use `approver: human:…`.
- Conventional commits; local review after each commit.

## Constructors & optics

Read **[reference.md](reference.md)** before hand-rolling primitives:

- `typekernel.draw.construct`: `hook`, `tensioned_arc`, `spring`, `diagonal_band`, `superellipse_quarter`
- `typekernel.plugins.construct.skeleton_pen`: `broad_nib`, `pointed_pen`, `expand_skeleton`
- `typekernel.optics.stem`: `measure_oriented_stem`, `diagonal_compensation`

## Anti-patterns

See **[anti-patterns.md](anti-patterns.md)** — especially「用基本形拼字」and「改期望表过检查」.

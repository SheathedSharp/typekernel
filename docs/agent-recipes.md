# Agent recipes (pointer + maintenance index)

> **Design method (ARCHITECTURE.md 标准工作流):** `tk new --starter latin-sans` → edit
> `system.py` / `glyphs/` / `elements.py` / `spacing.py` → `tk proof` /
> `tk audit` / `tk build`. See
> [`.agents/skills/typekernel-font-design/`](../.agents/skills/typekernel-font-design/SKILL.md)
> ([recipes](../.agents/skills/typekernel-font-design/recipes.md),
> [anti-patterns](../.agents/skills/typekernel-font-design/anti-patterns.md),
> [reference](../.agents/skills/typekernel-font-design/reference.md)).

`typekernel.parts` / `DesignContext` / `FormSources` / Usage B aggregates
(`Controls` / `DesignSequence` / `unlock_*` / `build_all`) are **deleted**. Do not
resurrect them.

## Product rule

| Do | Don't |
| --- | --- |
| Draw with `typekernel.draw` + `@glyph` in the project | Import `typekernel.parts` / `DesignContext` |
| Space via project `spacing.py` (metrics keys + kern) | Rely on bbox-only advances as the design |
| Compile with `tk build` / `tk build --variable` and proof | Add heal / blend / seal passes for bad joins |

## Maintenance CLIs

```bash
tk new myfont --starter latin-sans
tk build .
tk proof control .
tk audit .
tk build . --variable

# quickstart example
python examples/latin_sans_quickstart/build.py
```

Architecture contracts: [ARCHITECTURE.md](ARCHITECTURE.md) 交接规格.

### Starter patterns

Copy from `src/typekernel/starters/latin_sans/` (`elements.py`, `glyphs/**`,
`font.py` corner wiring, `spacing.py`). Kernel packages stay letter-free.

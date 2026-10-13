# Agent glyph preview

Coding agents: use this after changing `Controls`, spacing, or hook letters.

```bash
pip install -e ".[compile,specimen,boolean]"
python examples/agent_glyph_preview/build_preview.py
```

Outputs in `out/` (gitignored):

| File | Content |
| --- | --- |
| `TypekernelAgentPreview-Regular.otf` | Installable mini font |
| `grid.png` | Focus glyphs at large size |
| `sentence.png` | Default agent sentence at body size |

Custom focus set:

```bash
python examples/agent_glyph_preview/build_preview.py --chars "f t I a g"
```

Workflow: [`.agents/skills/typekernel-font-design/SKILL.md`](../../.agents/skills/typekernel-font-design/SKILL.md)

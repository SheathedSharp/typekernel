# Agent family (L2 template)

One step above [`agent_studio`](../agent_studio/): a **static family** with three designed masters. Copy this directory to `examples/<family>/` when the brief asks for weights, not a single trial.

| File | Role |
| --- | --- |
| `design.py` | `design_controls` / `design_light` / `design_bold` — replace the TODOs |
| `build_family.py` | `compose_font_from_controls`, shared kern classes, locked sentence gate |

Regular is checked against the unmodified preset (`optical_gap_ratio`, non-terminal G1) and needs two weak-glyph overrides. Light and Bold are separate sheets; Bold uses `with_stem_relief()`. They are not graded against Regular's preset.

Not in this template yet (see the TODOs and [`docs/agent-recipes.md`](../../docs/agent-recipes.md)):

- italic masters (`italic_controls`, not oblique shear)
- variable font
- `tnum` / `case` / extended Latin

```bash
pip install -e ".[compile,specimen,boolean]"
python examples/agent_family/build_family.py
```

Outputs in `out/` (gitignored): three OTFs, `proof.png` (locked sentence), `proof_brief.png`, `review/`.

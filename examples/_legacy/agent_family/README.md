# Agent family (L2 template)

Each master must pass `Controls.unlock_body` / `DesignSequence` before compose; `build_all` in `build_family.py` is compose-time derivation only.

One step above [`agent_studio`](../agent_studio/): a **static family** with three designed masters. Copy this directory to `examples/<family>/` when the brief asks for weights, not a single trial.

| File | Role |
| --- | --- |
| `design.py` | `design_controls` / `design_light` / `design_bold` — replace the TODOs |
| `build_family.py` | `compose_font_from_controls`, shared kern classes, locked sentence gate |

Regular is checked against the unmodified preset (`optical_gap_ratio`, non-terminal G1) and needs two weak-glyph overrides. Light and Bold are separate sheets; Bold uses `with_stem_relief()`. They are not graded against Regular's preset.

Related examples (not duplicated in this folder):

- Italic / `wght×ital` VF: [`italic_family`](../italic_family/) (`vf_italic_pair`)
- Static `wght` VF: [`variable_family`](../variable_family/)
- Trial baselines: [`agent_trial`](../agent_trial/) (`snapshot_presets.py`, `snapshot_serif_voices.py`)

Still on you for a copied family: `tnum` / `case` / extended Latin (see [`docs/agent-recipes.md`](../../docs/agent-recipes.md)).

```bash
pip install -e ".[compile,specimen,boolean]"
python examples/agent_family/build_family.py
```

Outputs in `out/` (gitignored): three OTFs, `proof.png` (locked sentence), `proof_brief.png`, `review/`.

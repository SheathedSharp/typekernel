# Agent studio (L0 trial)

**Coding agents start a trial by writing Python against typekernel** — brief, one named preset, a documented proportion delta, at least two weak-glyph masters, then proof.

This directory is **L0 only** (one Regular voice). A family — Light/Bold or a variable font, `compose_font_from_controls`, its own `build_*.py` — goes in [`examples/agent_family/`](../agent_family/) or a new `examples/<family>/`.

| File | Who edits |
| --- | --- |
| **`design.py`** | **Agent / you** — preset, documented `tuned`, `with_glyph` on two of `f t j a s e` |
| `build.py` | Repo — `design_review` + locked sentence gate + previews |

Body letters must pass `Controls.unlock_body` / `DesignSequence` before compose; `build_all` is compose-time only.

Pass/fail text is `AGENT_SENTENCE`. `BRIEF_SENTENCE` is written to `sentence_brief.png` and cannot make the gate pass. The trial must not worsen the unmodified preset's optical gap ratio or non-terminal G1.

```bash
pip install -e ".[compile,specimen,boolean]"
python examples/agent_studio/build.py
```

Outputs in `out/` (gitignored): OTF, `grid.png`, `sentence.png` (locked sentence), `sentence_brief.png`, `review/` (delta JSON + control PNGs). A failing gate exits non-zero.

Workflow: [`.agents/skills/typekernel-font-design/SKILL.md`](../../.agents/skills/typekernel-font-design/SKILL.md) · Goal: [`docs/AGENT_GOAL.md`](../../docs/AGENT_GOAL.md) · Recipes: [`docs/agent-recipes.md`](../../docs/agent-recipes.md)

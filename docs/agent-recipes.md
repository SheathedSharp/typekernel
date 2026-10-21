# Agent recipes (pointer + maintenance index)

> **Design method:** Usage A only — compose parts → `Font` → agent-chosen spacing →
> compile → proof. See [`.agents/skills/typekernel-font-design/`](../.agents/skills/typekernel-font-design/SKILL.md)
> ([parts-catalog](../.agents/skills/typekernel-font-design/parts-catalog.md),
> [recipes](../.agents/skills/typekernel-font-design/recipes.md),
> [anti-patterns](../.agents/skills/typekernel-font-design/anti-patterns.md)) and
> [AGENT_GOAL.md](AGENT_GOAL.md).

Usage B (`Controls` / `DesignSequence` / `unlock_*` / `build_all`) has been **deleted**.
Optional `FormSources.derive` is stock RELATED_FORMS sugar only — not the design method.

## Product rule

| Do | Don't |
| --- | --- |
| Write Python that composes `typekernel.parts` | Treat `FormSources.derive` as design |
| Space with `space_font` / manual advances | Require any unlock / DesignSequence gate |
| Compile with `build_font` and proof | Revive deleted Controls / build_all APIs |

## Maintenance CLIs (library keepers)

```bash
PYTHONPATH=src python examples/run_program_exit.py
PYTHONPATH=src python examples/human_review_bundle.py --only appendix-b --out artifacts/human-review
# proofs: appendix_b_three_g_humanist.png, appendix_b_s_opening_humanist.png (B-13–B-15)
PYTHONPATH=src python examples/contact_sheet.py
PYTHONPATH=src python examples/diff_overlay.py
PYTHONPATH=src python examples/regenerate_outline_hashes.py
PYTHONPATH=src python examples/weight_ladder_sheet.py
```

Trial helpers: `snapshot_trial`, `validate_trial_snapshot`, `trial_snapshot_exit_code`,
`require-human-scores`, `voice_distance` — see [AGENT_TRIALS.md](AGENT_TRIALS.md).

### Stress / gaps / specs

- `stress` / contrast: `tests/parts/test_stress.py`; letter cuts `_cut_x` / `control._cut`
- Counter pinch: `min_run_gap`, `0.09`, `COUNTER_GAP_FLOOR_OVER_STEM`,
  `test_counter_gap_floor_formula_frozen`,
  `test_descender_micro_sliver_below_min_run_gap_ignored`
- Weak glyph specs (`glyph_specs`, `GSpec`, `RSpec`, `YSpec`, `spec_fields`, `spec f:`):
  `tests/parts/test_glyph_specs.py`

### Skeleton spike (not default)

`trace_letter`, `polyline_to_cubic_centerline`, `examples/zayju_script/`
(`build_charset_sequential`), QA helpers `script_topology_skip_checks` /
`script_sequence_tolerances` / `style_consistency` — see
`tests/examples/test_zayju_script.py`, `tests/qa/test_style_consistency.py`.

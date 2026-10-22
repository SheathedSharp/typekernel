# Reference — maintenance CLIs & acceptance hooks

This file is **not** the design method. Design = Usage A (see [SKILL.md](SKILL.md)).
Keep these pointers so library maintainers can run program exits and human review.

## Program exit

```bash
# Yoke prefer locks (Usage A continuous path)
pytest -q tests/parts/test_builders_prefer_yokes.py tests/parts/test_opening_yokes.py
PYTHONPATH=src python examples/run_program_exit.py
# --gate all: §8 doc hooks + agent trial smoke + pending gate test_evidence
pytest -q tests/docs/test_development_plan_section8.py
pytest -q tests/qa/test_multi_voice_exit.py tests/qa/test_originality.py
pytest -q tests/parts/test_knob_coverage.py tests/qa/test_style_consistency.py
pytest -q tests/examples/test_zayju_script.py
```

Serif / italic program acceptance: `test_serif_voice_meets_program_acceptance`,
`test_italic_program_acceptance` (in `tests/parts/`).

## Human review bundle

```bash
PYTHONPATH=src python examples/human_review_bundle.py --only serif --out artifacts/human-review
PYTHONPATH=src python examples/human_review_bundle.py --only italic --out artifacts/human-review
PYTHONPATH=src python examples/human_review_bundle.py --only appendix-b --out artifacts/human-review
```

Appendix B proofs: `appendix_b_three_g_humanist.png`, `appendix_b_s_opening_humanist.png`
(B-13–B-15). Does **not** write `approvals/*.json`.

## Contact sheet / overlays / golden hashes

```bash
PYTHONPATH=src python examples/contact_sheet.py
PYTHONPATH=src python examples/diff_overlay.py
PYTHONPATH=src python examples/regenerate_outline_hashes.py
PYTHONPATH=src python examples/weight_ladder_sheet.py
```

## Trial snapshots (legacy examples)

```bash
PYTHONPATH=src python examples/_legacy/agent_trial/snapshot_design.py …
PYTHONPATH=src python examples/_legacy/agent_trial/validate_snapshot.py
PYTHONPATH=src python examples/_legacy/agent_trial/snapshot_serif_voices.py
```

APIs: `snapshot_trial`, `validate_trial_snapshot`, `trial_snapshot_exit_code`,
`--require-human-scores`, `program-snapshot-only`. See `docs/AGENT_TRIALS.md`.

## Stress / contrast / counter gaps

- `stress` on `DesignContext` — rounds; regressions in `tests/parts/test_stress.py`
- Letter-builder cuts may mention `_cut_x` / `control._cut`
- Weight ladder / pinch: `min_run_gap`, floor `0.09`, `COUNTER_GAP_FLOOR_OVER_STEM`,
  `test_counter_gap_floor_formula_frozen`,
  `test_descender_micro_sliver_below_min_run_gap_ignored`

## Skeleton / script spike (not default design)

`trace_letter`, `polyline_to_cubic_centerline`, example `examples/zayju_script/`
(`build_charset_sequential`). Library helpers `try_unlock_script_builders` /
`style_consistency` live under `typekernel.qa` for sequential QA — **not** the
Usage A happy path. Tests: `test_zayju_script.py`, `test_style_consistency.py`.

## Weak-glyph specs (legacy FormSources surface)

If you still touch `tuned_glyph` on legacy FormSources sheets: see `parts/glyph_specs.py`
(`GSpec`, `RSpec`, `YSpec`, `spec_fields`, e.g. `spec f:`). Regressions:
`tests/parts/test_glyph_specs.py`.

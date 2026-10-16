# Approvals

Human decision records for typekernel visual and API gates.

Each file under this directory is a small JSON document a person writes after
reviewing a change (for example a public API surface, an optical correction, or
a specimen PNG). Agents and scripts may **read** these files and may help draft
them, but they must not mark a gate as approved without an explicit human
decision.

## Schema

Required fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `gate` | string | Stable id for the decision (human-readable kebab-case) |
| `approved` | boolean | `true` only after a human said yes |
| `approver` | string | Who approved (or empty while pending) |
| `date` | string | ISO date `YYYY-MM-DD` |
| `notes` | string | What was judged and any caveats |

Optional extras such as `scope` or `test_evidence` are allowed.

Helpers live in `typekernel.qa.gates`:

- `write_approval(...)` — persist a record (does not decide for you)
- `load_approval(path)` — read and validate
- `require_approval(path)` — raise if missing or not approved

## Naming

Prefer plain names that describe the decision, for example:

- `geo-public-api.json`
- `optical-overshoot.json`
- `specimen-synthetic-o.json`
- `serif-slab-voice.json` / `serif-bracketed-voice.json` — after reviewing proofs from `examples/human_review_bundle.py` (see `docs/agent-recipes.md`)
- `italic-vf-construct.json` — after reviewing `examples/italic_family` VF from the same bundle (`--only italic`)

Avoid internal planner ticket codes in file names or field values.

## Pending templates (not approved)

These ship with ``approved: false`` until a human updates them after review:

- `serif-slab-voice.json` / `serif-bracketed-voice.json` — `--only serif` (slab/bracketed `proof.png`, VF `proof_vf.png`, weight ladder PNGs)
- `italic-vf-construct.json` — `--only italic` (review `proof.png`, `proof_vf.png`, VF `.ttf` under `italic_family/`)

**Appendix B-15 (`s` opening)** has no JSON gate: review `tk206_s_opening_humanist.png` from
`human_review_bundle.py --only tk206` (or `contact_sheet.py --chars sS`). Record acceptance in
notes or a design log only; changing `S_OPENING_REACH_RELIEF` requires golden refresh per
`docs/agent-recipes.md`.

Generate local proofs (does not write this folder):

```bash
PYTHONPATH=src python examples/human_review_bundle.py --out artifacts/human-review
```

Before signing, run the `test_evidence` paths on each JSON file and the programmatic checks in `REVIEW_CHECKLIST.md` (for example `tests/parts/test_serifs.py::test_serif_voice_meets_tk306_program_acceptance` and `tests/parts/test_italic_program_acceptance.py`). See `tests/docs/test_development_plan_section8.py` for `DEVELOPMENT_PLAN` §8 hooks.

### Copy-paste program checks (pending gates)

From repo root, after opening `artifacts/human-review/` (or your `--out` path):

**`serif-slab-voice.json`**

```bash
pytest -q \
  tests/examples/test_slab_serif.py \
  tests/examples/test_human_review_bundle.py \
  tests/parts/test_serifs.py::test_serif_voice_meets_tk306_program_acceptance \
  tests/qa/test_m3_exit.py \
  tests/qa/test_originality.py \
  tests/qa/test_sentence_gate.py \
  tests/docs/test_development_plan_section8.py
```

**`serif-bracketed-voice.json`**

```bash
pytest -q \
  tests/examples/test_bracketed_serif.py \
  tests/examples/test_human_review_bundle.py \
  tests/parts/test_serifs.py::test_serif_voice_meets_tk306_program_acceptance \
  tests/qa/test_m3_exit.py \
  tests/qa/test_originality.py \
  tests/qa/test_sentence_gate.py \
  tests/docs/test_development_plan_section8.py
```

**`italic-vf-construct.json`**

```bash
pytest -q \
  tests/examples/test_human_review_bundle.py \
  tests/examples/test_italic_family.py \
  tests/parts/test_italic_program_acceptance.py \
  tests/parts/test_italic_controls.py \
  tests/parts/test_italic_topology.py \
  tests/parts/test_oblique_compat.py \
  tests/docs/test_development_plan_section8.py
```

Then update the JSON (`approved`, `approver`, `date`, `notes`) or use `write_approval` as in `examples/human_review_bundle.py` → `REVIEW_CHECKLIST.md`.

### After you approve a gate (maintainer)

1. Re-run that gate’s program checks (above) so evidence matches the commit you are on.
2. Set `approved: true`, fill `approver` / `date` / `notes` (keep `test_evidence` paths accurate).
3. Update `tests/docs/test_development_plan_section8.py`: remove the signed gate from `_PENDING_HUMAN_GATES` (and mirror any `_PENDING_GATE_JSON` lists in `tests/qa/test_gates.py`) so CI no longer expects `approved: false` for that file. When **all three** visual gates are signed, `test_section8_human_gates_remain_pending_until_review` should be removed or rewritten to assert the approved records instead.
4. Run `PYTHONPATH=src python examples/run_m5_program_exit.py --full-suite --with-linters` (or `pytest -q` + ruff + mypy) before pushing — do not relax `AGENT_SENTENCE` or L3 thresholds.

Agents must not flip ``approved`` to ``true`` without explicit human instruction.

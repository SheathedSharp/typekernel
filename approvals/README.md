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

- `serif-slab-voice.json` / `serif-bracketed-voice.json` — proofs via `examples/human_review_bundle.py --only serif`
- `italic-vf-construct.json` — `--only italic`

Agents must not flip ``approved`` to ``true`` without explicit human instruction.

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
`test_evidence` is either a list of repo-relative test paths — CI checks that
each one exists — or an object recording observed command results
(`{"pytest": "473 passed", …}`).

Helpers live in `typekernel.qa.gates`:

- `write_approval(...)` — persist a record (does not decide for you)
- `load_approval(path)` — read and validate
- `require_approval(path)` — raise if missing or not approved

`tests/qa/test_gates.py` loads every JSON in this directory, so a record that
does not validate fails CI.

## Current gates

| File | Decision |
| --- | --- |
| `geo-public-api.json` | `typekernel.geo` public API surface and the cubic-first story |
| `optical-overshoot.json` | `optics.overshoot.apply_overshoot` v0 for round glyphs |
| `font-model.json` | `typekernel.font` public API (Font / Glyph / Master / Component / kerning) |
| `compile-bridge.json` | `typekernel.compile` build bridge (UFO → ttf / otf / woff2, VF, round-trip) |

## Naming

Prefer plain names that describe the decision, for example
`geo-public-api.json` or `optical-overshoot.json`. Avoid internal planner
ticket codes in file names or field values.

## Adding a gate

1. Write the JSON with `approved: false` and the evidence you expect to cite
   (`test_evidence` lists repo-relative test paths).
2. Have a human review the artifact and the evidence.
3. Only then set `approved: true` and fill `approver` / `date` / `notes`.

Keep `test_evidence` paths real — they are what a later reader re-runs to check
the decision still holds.

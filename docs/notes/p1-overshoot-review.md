# Optical overshoot review (synthetic O)

**Status: awaiting human approval.** Do not treat this note as a passed gate.

## What to look at

1. Numeric dump: [`artifacts/specimens/O_overshoot_coords.txt`](../../artifacts/specimens/O_overshoot_coords.txt)
2. Implementation: `typekernel.optics.overshoot.apply_overshoot`
3. Pipeline: `typekernel.optics.pipeline.apply(..., overshoot=True)`

## Expected numbers (UPM 1000, `OpticalContext.latin_defaults`)

| | ymin | ymax |
| --- | --- | --- |
| Before | 0 | 700 |
| After (`overshoot_round=12`) | −12 | 712 |

Delta = ±12 on the control-point AABB. For this synthetic O the flat top/bottom
handles already share the extrema y, so they move with the on-curve points
(naive handle policy documented in `overshoot.py`).

## How to regenerate the dump

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
from typekernel.geo.fixtures import load_synthetic_outline
from typekernel.geo.outline import bounds
from typekernel.optics.context import OpticalContext
from typekernel.optics.overshoot import apply_overshoot

o = load_synthetic_outline("tests/fixtures/synthetic_O.json")
ctx = OpticalContext.latin_defaults()
print("before", bounds(o))
print("after ", bounds(apply_overshoot(o, ctx, kind="round")))
PY
```

## Review checklist for the human

- [ ] ymax increased by about `overshoot_round` (12)
- [ ] ymin decreased by about `overshoot_round` (12)
- [ ] Input outline is not mutated (tests cover this)
- [ ] Accept that v0 is outline-wide / naive handles (counter also moves)
- [ ] Confirm this is **not** stroke expand / buffer weight

## Approval artifact

When satisfied, record approval in `approvals/GATE-P1-OVERSHOOT.json` with
`"approved": true` (human only). This note intentionally leaves that file unset.

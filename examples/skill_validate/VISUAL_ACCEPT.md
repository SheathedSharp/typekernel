# Visual accept (vision agent only)

Code smoke (pytest / `run_validate`) must **not** claim visual PASS. Ship/reject
is decided by reading proof PNGs.

## Proofs to read

Prefer the `visual_accept_*.png` pack (also copied under `/workspace/uploads/`):

| File | Focus |
| --- | --- |
| `visual_accept_stems.png` | `n h m r u` — continuous shoulders, no stitch look |
| `visual_accept_diags.png` | `v w x y k` — crotches readable, not clipped to a slab |
| `visual_accept_ag.png` | single `a`/`g` (defaults) + optional double forms |
| `visual_accept_caps.png` | sample capitals `A H O N V` |
| `visual_accept_figs.png` | lining `0–9` |
| `visual_accept_ladder.png` | weight ladder (light → bold) on a short word |

Also useful: `artifacts/skill-validate/proof_*.png` from `run_validate.py`.

## Must check

1. **Joins continuous** — stem↔shoulder / stem↔bowl / diagonal crotches look sealed; no hairline white slits or kit-of-parts seams at intended joins.
2. **No stitch look** — bodies read as one letter, not boolean leftovers or floating contours.
3. **Counters open** — bowls/eyes are readable holes at light and bold (not filled slabs, not collapsed pinches).
4. **Weight ladder stable** — light→bold keeps topology; no disappearing bowls, exploding blobs, or .notdef boxes in the proof string.
5. **Part exits** — if a public yoke/builder produces a bad shape, **reject and remake the part**; do not paper over with a numeric gate in tests.

## Must not

- Auto-PASS from hairline scans, spring-band white-gap asserts, or ink width-delta thresholds.
- Treat smoke-green as ship.

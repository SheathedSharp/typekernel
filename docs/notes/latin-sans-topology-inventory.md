# latin-sans topology inventory (agent-actionable)

> Snapshot 2026-10-29 (g rewrite + UC edge/mid_right cues). No `approved: true`.

## `tk read` metrics

| Sample | top1 | hard warn | near-tie |
| --- | --- | --- | --- |
| `hamburgefonstiv` | 15/15 | 0 | 0 |
| `a–z` | 26/26 | 0 | 0 |
| `A–Z` | 26/26 | 0 | 0 |
| cold trial lc string | 17/17 | 0 | 0 |

## Design choice: `g` double-storey

Chose **double-storey** (upper bowl + right stem + lower bowl), matching the
binocular construction language already used for latin-sans. Topology target:
**2 counters, 1 island**. `expect.py` 3→2 with review rationale.
Knowledge prior: primary `counters=2`, `counters_alt=(1,)` so single-storey
script faces stay valid (platform storey-variant, not a string hack).

## Closed

| Glyph | Fix |
| --- | --- |
| `k` | stem → ascender |
| `B` | bowls meet at waist; expect 3→2 |
| `G` | aperture + spur; open-G prior counters=0 |
| `w`/`W` | overlapping diagonal_pairs |
| `g` | double-storey rewrite; expect 3→2 |

## Platform cue additions (C3)

- `edge_mass` — outer-column ink (N/H vs Z/X/bowls)
- `mid_right` — mid-band right half (G spur vs C)
- `counters_alt` — alternate counter counts for storey variants

## Still open (structural, non-blocking)

- None known for Basic Latin topology vs letter-class priors on latin-sans.
- Aesthetics / SCORE / VISION remain human.

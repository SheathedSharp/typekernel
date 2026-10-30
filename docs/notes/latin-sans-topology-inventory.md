# latin-sans topology inventory (agent-actionable)

> Snapshot 2026-10-29 (post C3 read + topology fixes). Letter-class priors live in
> `typekernel.knowledge`; mismatches are **starter glyph debts**, not reasons to
> special-case strings. No `approved: true`.

## `tk read` metrics

| Sample | top1 | hard warn | near-tie |
| --- | --- | --- | --- |
| `hamburgefonstiv` | 15/15 | 0 | 0 |
| `a–z` | 26/26 | 0 | 0 |
| `A–Z` | 23/26 | 0 | (near-ties possible on N/O family) |
| cold trial lc string | 17/17 | 0 | 0 |

Hard-warn policy: topology mismatch (or confuse-pair counters) only.

## Closed this batch

| Glyph | Was | Fix |
| --- | --- | --- |
| `k` | stem to x-height only (missing asc) | stem → `zones.asc` |
| `B` | counters 3 | bowls meet at waist → 2; `expect.py` 3→2 with review rationale |
| `w` / `W` | islands 2 | overlapping diagonal_pairs → 1 island; A/W kern nudged |
| `G` | islands 2, open class | tighter aperture + spur into bowl → 1 island; prior counters=0 (open G) |

## Still open

| Glyph | Measured vs prior | Notes |
| --- | --- | --- |
| `g` | counters 3 vs prior 1 | binocular bowls + ear; `expect.py` still documents 3 as starter baseline until a clean 1–2 counter rewrite |

## Not holes

- UC near-ties among same-topology peers — improve cues later; no string special-cases.
- script-roundhand shape rank noise with matching topology — info only by design.

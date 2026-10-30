# latin-sans topology inventory (agent-actionable)

> Snapshot 2026-10-29. Letter-class priors live in `typekernel.knowledge`;
> mismatches below are **starter glyph debts**, not reasons to special-case
> strings or soften `expect.py`. No `approved: true`.

## `tk read` baseline (after C3 shape bins)

| Sample | top1 | hard warn | near-tie |
| --- | --- | --- | --- |
| `hamburgefonstiv` | 15/15 | 0 | 0 |
| `a–z` | 26/26 | 0 | 0 |
| `A–Z` | 23/26 | 1 (`G`) | 2 (`N`,`O`) |
| cold trial lc string | 17/17 | 0 | 0 |

Hard-warn policy: topology mismatch (or confuse-pair counters) only; same-topology
shape rank fights stay `info` so other styles are not false-failed.

## Clear holes (fix glyph, not prior)

| Glyph | Measured vs letter-class prior | Likely cause | Suggested fix direction |
| --- | --- | --- | --- |
| `k` | was missing ascender (stem to x-height only) | stem stopped at `xh` | **Fixed this batch**: stem → `zones.asc` |
| `g` | counters 3 vs prior 1 (letter-class single-storey; binocular forms often 2) | two bowls + ear create extra cavities / slits | merge ear into bowls; target 1–2 clean counters, not 3 |
| `B` | counters 3 vs prior 2 | bowl joins / slit | reseal counters to 2 without heal — fix join geometry |
| `G` | counters 0 / islands 2 vs prior 1 / 1 | `open_bowl` + floating `crossbar` spur | join spur into bowl so one counter + one island; or redesign as closed G |
| `w` / `W` | islands 2 vs prior 1 | diagonal overlaps leaving a slit island | join diagonals cleanly; one outer island |

## Not holes (do not “tune away”)

- UC near-ties `N`↔`Z`, `O`↔`D` — same coarse topology family; shape bins still weak. Improve generalized cues later; do not add string special-cases.
- script-roundhand cold-string shape rank noise — topology hard-warns suppressed by design when topology matches; RH glyph tuning is out of scope for this inventory.

## Audit

Stock `latin-sans` remains the structural 0/0 audit bar for stems/zones unless a
glyph edit reopens a check. Re-run `tk audit` after each glyph fix.

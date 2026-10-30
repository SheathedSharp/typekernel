# latin-sans Ext-A / punct inventory (agent-actionable)

> Snapshot 2026-10-30. No `approved: true`. Aesthetics left to human.

## Fixed this stretch

| Glyph | Was | Fix |
| --- | --- | --- |
| `parenright` | islands=3 (self-crossed cup) | mirror of working `parenleft` → islands=1 |
| `ae` / `oe` | counters 1 (unstable across masters) | two overlapping bowls → 2/1 Light+Bold |
| `OE` | counters 3 (bar cage) | two bowls + light mid bar → 2/1 |
| `AE` | islands 2 / lerp warns; then open join (c=1) but read as Q/A | **A triangle + E bars** (c=1/i=1 master-stable); `LATIN_EXT` digraph priors so `tk read` tops AE/OE/ae/oe |

`expect.py` entries for AE/ae/OE/oe/parenleft/parenright (topology unchanged for AE this round: still 1/1).

## Platform (not glyph-string)

- `LATIN_EXT` TopologyPriors for AE/ae/OE/oe; `_latin_rank_pool` includes Ext digraphs.
- Partial Tracy: `tracy_bands` + `tracy_ink` (scanline ink-fraction columns).

## Still open / ambiguous (document, do not force)

| Glyph | Notes |
| --- | --- |
| `Oslash` / `oslash` | slash through O measures counters=2; letter-class sometimes cited as 1 — geometric split is honest |
| `ampersand` | open construction, counters=0 — stylistic |
| `at` | islands=2 (outer + inner a) — plausible |
| `germandbls` | counters=2 vs some 1-counter ß designs |
| `Eth` / `Hbar` / `IJ` | minor class debates; not blocking audit |

## Gates

latin-sans `tk audit` 0 error / 0 warn; Basic Latin `tk read` a–z/A–Z 26/26; digraph intended reads top AE/OE/ae/oe (AE may near-tie A historically; now tops AE).

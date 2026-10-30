# latin-sans Ext-A / punct inventory (agent-actionable)

> Snapshot 2026-10-30. No `approved: true`. Aesthetics left to human.

## Fixed (clear structural / letter-class)

| Glyph | Was | Fix |
| --- | --- | --- |
| `parenright` | islands=3 | mirror of `parenleft` → 1 |
| `ae` / `oe` / `OE` | unstable / bar cage | bowls → 2/1 |
| `AE` | read as Q/A | A-triangle + E bars; `LATIN_EXT` prior |
| `Eth` | c=0 (`bowl_join` open) | closed bowl + stem stroke → **1/1** like D |
| `dcroat` | Bold c=2 | ascender-only stroke → **1/1** both masters |
| `hbar` | Bold slit | higher ascender stroke → **0/1**, slots=0 |
| `IJ` | islands=3 (free hook) | J hook joined → **0/2** |
| `ij` | islands=4 | kept **0/4** (2 bodies + 2 dots); hook joined |

## Platform

- `LATIN_EXT` priors for digraphs + barred/thorn/eth family; **injected into read pool only when `intended_cp` is Ext** (does not displace A–Z top-1).
- Partial Tracy only; no bitmap Tracy.

## Deferred (design-ambiguous — do not force)

| Glyph | Why deferred |
| --- | --- |
| `Oslash` / `oslash` | Slash splits O → c=2; some letter-class cites 1 |
| `ampersand` / `at` | Stylistic island/counter choices |
| `germandbls` | Light c=2 / Bold c=1 under wght; ß letter-class 1 vs 2 is design choice — forcing either side overfits or trips gray/zone |
| `Hbar` | Dual bars seal c=1 while H is c=0 — barred-H geometry OK |
| `Eng` / `Lslash` / `Tbar` / `Ldot` / `longs` / `kgreenlandic` | No audit/topology flip; aesthetics HUMAN |

## Gates

`tk audit` 0/0; Basic Latin `tk read` 26/26.

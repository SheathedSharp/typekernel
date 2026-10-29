# Anti-patterns

## 用基本形拼字

Do not assemble letters from bare rectangles + rings (θ-shaped `e`, figure-8 `three`,
crossed-arc parentheses). Use anatomy constructors / tensioned arcs / open bowls once
Until the anatomy parts ship, prefer starter fragments and fix joins in project code — never
heal/blend/seal.

Appendix A counterexamples (unmodified latin-sans): `e` (2 counters), `three` (≥2),
`parenleft`/`parenright` density outliers — `tk explain` / `tk audit` report these.

## 改期望表过检查

Never edit `expect.py` (or relax baselines) solely to make `tk audit` green.
Expect encodes *correct* topology/reach. If a glyph is wrong, change the glyph.
If expect itself must change, record the reason in `tk review record … --note`.

## Other

- heal / blend / seal on the default path
- letter-name tables in the kernel
- agent writing `approved: true` into `approvals/`
- inventing private PIL croppers instead of `tk see` / `tk proof`

# P6-3 kernel / process backlog

Gaps found while transplanting LihuiT into typekernel:

1. **Static Bold ≠ Regular topology** — published LihuiT Regular/Bold have
   different point counts, so they cannot share a VF Light↔Bold master pair
   under G-class. Dogfood ships a single Regular master; Bold is compared via
   `ref_outlines` weight select. *Need:* optional multi-static export without
   InterpolationCheck, or a redesign path that keeps Bold interpolatable.
2. **Project top-level modules** — bare imports only resolve
   `_TOP_LEVEL_CANDIDATES`. Added `ref_outlines` for this dogfood; future
   transplant helpers need the same allowlist or live under `elements.py`.
3. **Metrics packing vs absolute transplants** — **done (warm track):**
   `Metrics.pack="absolute"` keeps drawing x-origin (no LSB re-shift) and sets
   `advance = max_x + rsb`. Dogfood `spacing.py` uses it. Exact published
   `hmtx` advances remain optional polish (Stem RSB ≈ OFL RSB for most glyphs).
4. **Parametric rewrite (optional follow-up)** — current glyphs load published
   outlines into Drawings. A true parametric port of `outline_engine.Designer`
   would let agents edit construction, not only transplant.

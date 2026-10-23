# Skill validate (Usage A × 2 recipes)

Runs the geometric UI sans brief from `.agents/skills/typekernel-font-design/SKILL.md`
two ways (letter builders vs raw yokes with distinct params), compiles OTFs, writes
proofs under `artifacts/skill-validate/`.

```bash
PYTHONPATH=src python examples/skill_validate/run_validate.py
# optional: emit vision-review pack into /workspace/uploads (or --out-dir)
PYTHONPATH=src python examples/skill_validate/emit_visual_accept.py
```

## Smoke vs ship

| Layer | What it means |
| --- | --- |
| **Smoke green** | Builds, exports, cmap/API/packing/VF segment invariants — **not** visual quality. |
| **Ship** | A **vision agent** (or human) reads proof PNGs per `VISUAL_ACCEPT.md` and accepts or rejects. |

Do **not** treat pytest / `run_validate` exit 0 as “looks good.” Reject bad part exits and remake; do not add numeric white-gap / hairline / width-delta “quality PASS” gates back into code.

See `artifacts/skill-validate/COMPARE.md` after a run. Not full agent / human-gate validation.

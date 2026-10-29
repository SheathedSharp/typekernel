# LihuiT transplant (typekernel)

Redraws **LihuiT Regular/Bold lowercase a–z + lining figures 0–9** as typekernel
Drawings loaded from the published OFL faces (oh-my-font), then measures
symmetric Hausdorff distance.

## Status

| Face | median | p95 | target |
| --- | --- | --- | --- |
| Regular | 0 | 0 | ≤8 / ≤20 |
| Bold | 0 | 0 | ≤8 / ≤20 |

Single Regular master (Bold static topology ≠ Regular). See `BACKLOG.md`.

## Commands

```bash
.venv/bin/python transplants/lihuit/scripts/compare_hausdorff.py
```

Override refs with `LIHUIT_REGULAR` / `LIHUIT_BOLD`.

## Spacing

`METRICS.pack="absolute"` — transplanted outlines already include OFL LSB; packing must not re-shift ink.

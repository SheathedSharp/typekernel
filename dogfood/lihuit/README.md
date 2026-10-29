# P6-3 LihuiT dogfood (typekernel transplant)

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
.venv/bin/python dogfood/lihuit/scripts/compare_hausdorff.py
```

Override refs with `LIHUIT_REGULAR` / `LIHUIT_BOLD`.

# P6-3 LihuiT dogfood (typekernel transplant)

Separate workspace (not a `tk new` starter) that redraws **LihuiT Regular /
Bold lowercase + lining figures** with typekernel, then compares geometry to
the published OFL faces in oh-my-font.

Bootstrapped from `latin-sans` (`tk new --starter latin-sans`); glyphs will be
retargeted to LihuiT metrics. Do **not** treat stock starter shapes as the
dogfood target.

## Targets

| Face | Default path |
| --- | --- |
| Regular | `../../oh-my-font/dist/ttf/LihuiT/LihuiT-Regular.ttf` |
| Bold | `../../oh-my-font/dist/ttf/LihuiT/LihuiT-Bold.ttf` |

Override with `LIHUIT_REGULAR` / `LIHUIT_BOLD`.

## Metrics (roadmap §7 P6-3)

After UPM / advance alignment:

- Symmetric Hausdorff distance per glyph (font units)
- **median ≤ 8**, **p95 ≤ 20**
- Specimen juxtaposition → human approve
- Kernel gaps → backlog

## Commands

```bash
# from typekernel repo root
.venv/bin/python dogfood/lihuit/scripts/compare_hausdorff.py
tk build dogfood/lihuit
```

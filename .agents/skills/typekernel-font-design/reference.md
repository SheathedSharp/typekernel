# Reference

## CLI

| Command | Role |
| --- | --- |
| `tk new NAME --starter latin-sans` | Copy starter (system, elements, glyphs, spacing, font) |
| `tk build [PATH]` | Project → Font → UFO/OTF (default) |
| `tk build --variable` | Light / Regular / Bold → designspace + VF |
| `tk proof SET [PATH]` | `control` \| `spacing` \| `kern` \| `charset` \| `ladder` \| `all` |
| `tk proof --text "…" [PATH]` | Arbitrary string → `proofs/text.png` (set optional) |
| `tk proof --glyph n [PATH]` | Zoomed crop → `proofs/glyph-n.png` |
| `tk audit [PATH]` | stem / zone / direction / master-compat diagnostics |
| `tk audit --overlap` | Opt-in: ink∩ink even-odd cavity warnings (noisy on intentional VF overlaps) |
| `tk pen --contrast C --angle A` | Broad-nib effective-width preview by stroke direction |
| `tk diff [PATH]` | changed glyphs via `outline_hash` (`--snapshot` / `--against`) |

`tk proof` accepts `--size N` for pixel size of `--text` / `--glyph` / control.

## System

```python
from typekernel.system import Overshoot, System, Zones

system = System(
    upm=1000,
    zones=Zones(base=0, x=520, cap=700, asc=740, desc=-200),
    overshoot=Overshoot(round=12, pointed=10),
    stem={"lc": 84, "lc_h": 70, "uc": 92, "uc_h": 76},
    tokens={"n_width": 430, "lsb_lc": 40, "n_advance": 510, ...},
)
light = system.tuned(stem={k: v * 0.62 for k, v in dict(system.stem).items()})
```

Optional in the same `system.py` module — stroke kinds for `tk audit` optical probes:

```python
AUDIT_STEMS = {
    "n": ("vertical",),   # default for upright letters when omitted
    "v": ("diagonal",),   # use measure_oriented_stem (+ vertical_equiv)
    "w": (),              # named stem.*.foot nodes only; no optical fallback
    "x": "none",          # alias for ()
}
```

Letters without upright stems (`v w x y z s e o …`) skip optical **vertical**
probes by default (avoids false noise). Declare `"diagonal"` only when you want
oriented optical checks.

No `aperture` / `roundness` mega-knobs（见 ARCHITECTURE.md「System」）. Derived relations go in project `elements.py`.

## draw.construct (letter-free)

```python
from typekernel.draw import hook, tensioned_arc, spring, diagonal_band, superellipse_quarter

tensioned_arc(p0, t0, p1, t1, *, tension=0.55) -> Fragment
spring(stem_edge_x, y_from, y_to, toward, *, depth, tension) -> Fragment
hook(stem_edge_x, y_join, tip, *, depth, tension=0.55, tip_tangent=None) -> Fragment
diagonal_band(p_top, p_bottom, *, weight, compensate=True) -> (Fragment, Fragment)
superellipse_quarter(center, rx, ry, quadrant, *, exponent) -> Fragment
```

Do **not** reimplement entry / exit / flourish arcs in the project when these fit.
Signatures also live in ARCHITECTURE.md「几何构造器」.

## skeleton pen (construct plugin)

```python
from typekernel.plugins.construct.skeleton_pen import broad_nib, pointed_pen, expand_skeleton

pen = broad_nib(stem, contrast=0.26, angle_deg=30)
drawing = expand_skeleton(centerline, pen, join="miter")  # closed + round join → compat risk
```

Preview what a pen does: `tk pen --contrast 0.26 --angle 30 --thickness 100`.

## optics.stem

```python
from typekernel.optics.stem import (
    measure_oriented_stem,
    diagonal_compensation,
    vertical_equiv_from_diagonal,
    list_vertical_stems,
)

# Perpendicular thickness at origin along stroke bearing (0°=+x, 90°=+y)
w = measure_oriented_stem(outline, (cx, cy), direction_deg=45)

# Construction aid: perp thickness so a diagonal matches an upright stem optically
perp = diagonal_compensation(angle_from_vertical_deg=45, stem=84, contrast=1.0)

# Invert: recover upright-equivalent from a measured diagonal thickness
equiv = vertical_equiv_from_diagonal(measured_perp, angle_from_vertical_deg=45)
```

`tk audit` uses named `stem.*.foot.o/i` nodes first; optical vertical fallback is
gated by `AUDIT_STEMS` / the non-vertical default set. Prefer tagged nodes.

## @glyph

```python
from typekernel.project import glyph
from typekernel.system import System

@glyph("n", group="lc.straight")
def n(system: System):
    ...
    return left + right + trough  # Drawing; overlap OK
```

Master override: `@n.master("Bold")` on a second function of the same shape.

## font.py

```python
from typekernel.plugins.corners import plain
from typekernel.project import Project

def get_project() -> Project:
    return Project(system, ROOT / "glyphs", masters=masters, corners={"*": plain()})
```

## spacing.py

Declare Tracy / Glyphs-style metrics keys and kern pairs; `tk build` calls `apply_spacing`
so ink is packed to LSB and `advance = lsb + ink + rsb`.

## Plugins

- `typekernel.plugins.corners` — `plain`, `rounded`, `slab`, …
- `typekernel.plugins.ends` — `flat`, `angled`, `ball`, …
- `typekernel.plugins.passes` — `overshoot`, `diagonal_comp`, `crotch_thin` (call from glyph code when needed; still not heal/blend/seal)
- `typekernel.plugins.construct` — `skeleton_pen` (`broad_nib` / `expand_skeleton`)
- `typekernel.plugins.checks` — `direction` / `stem` / `zone` / `compat` / `overlap`; append project rules via `EXTRA_CHECKS` in `system.py`

## Proof strings (starter defaults)

```
control:  nnonoo  nnhnnhnn  oobobboo  HHOHOO
spacing:  hamburgefonstiv
kern:     AV Ta To Yo LT P. F,
```

## Overlaps & self_union

- **Design-time:** `Drawing.__add__` overlap is the recommended VF construction. Do **not**
  call `geo.boolean.self_union` to paper over bad joins (that is seal).
- **Perception:** `tk audit --overlap` reports ink∩ink pairs that cancel under even-odd
  preview (actionable: `tk proof --glyph`, reshape fragments). Noisy on intentional
  overlaps — use when hunting cavities, not as a default gate.
- **Static export:** `tk build --resolve-overlaps` turns on ufo2ft `removeOverlaps` for
  static OTF/TTF/WOFF2 only (packaging, recorded in the build manifest). **Forbidden**
  with `tk build --variable` — VF must keep overlapping masters. Not a design-time heal.

## Skeleton densify

- `ellipse_point_count(rx, ry, chord_budget=0.5)` picks a stable oval `n` — prefer this
  over guessing. Use Regular metrics and reuse the same `n` on Light/Bold.
- `expand_skeleton(..., chord_budget=…)` opt-in Catmull–Rom densify. Default is off
  (`None`) so weight-scaled centerlines do not change point counts under VF.

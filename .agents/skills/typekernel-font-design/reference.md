# Reference (post-M4)

## CLI

| Command | Role |
| --- | --- |
| `tk new NAME --starter latin-sans` | Copy starter (system, elements, glyphs, spacing, font) |
| `tk build [PATH]` | Project → Font → UFO/OTF (default) |
| `tk build --variable` | Light / Regular / Bold → designspace + VF |
| `tk proof SET [PATH]` | `control` \| `spacing` \| `kern` \| `charset` \| `all` |
| `tk audit [PATH]` | stem / zone / direction / master-compat diagnostics |
| `tk diff [PATH]` | changed glyphs via `outline_hash` (`--snapshot` / `--against`) |

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

No `aperture` / `roundness` mega-knobs (§9.7). Derived relations go in project `elements.py`.

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

## Proof strings (starter defaults)

```
control:  nnonoo  nnhnnhnn  oobobboo  HHOHOO
spacing:  hamburgefonstiv
kern:     AV Ta To Yo LT P. F,
```

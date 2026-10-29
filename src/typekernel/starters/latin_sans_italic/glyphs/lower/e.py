"""Control e — open_bowl + crossbar via anatomy.pen."""

from __future__ import annotations

from elements import open_bowl, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("e", group="control")
def e(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    width = float(system.tokens["o_width"]) * 0.96
    lsb = float(system.tokens["lsb_lc"])
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    cy = xh / 2.0
    rx = width / 2.0 - st * 0.1
    ry = xh / 2.0 + ov * 0.45 - st * 0.1
    bowl = open_bowl(system, cx=cx, cy=cy, rx=rx, ry=ry, thickness=st, open_side="right")
    bar_y = cy - ry * 0.05
    bar = stroke(system, [(cx - rx * 0.8, bar_y), (cx + rx * 0.4, bar_y)], thickness=thin)
    return bowl + bar

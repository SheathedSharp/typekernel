"""o-group glyph e — oval + crossbar (skeleton+pen)."""

from __future__ import annotations

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("e", group="lc.bowl")
def e(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("o_width", 420.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    cy = xh / 2.0
    rx = width / 2.0 - st * 0.1
    ry = xh / 2.0 + ov * 0.5 - st * 0.1
    bowl = stroke(system, oval_points(cx, cy, rx, ry), closed=True, thickness=st)
    bar_y = xh * 0.52
    bar = stroke(
        system,
        [(cx - rx * 0.85, bar_y), (cx + rx * 0.85, bar_y)],
        thickness=st * 0.85,
    )
    return bowl + bar

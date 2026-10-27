"""colon — two stacked dots (skeleton+pen)."""

from __future__ import annotations

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("colon", group="punct")
def colon(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    r = st * 0.42
    lsb = float(system.tokens.get("lsb_lc", 36.0)) * 0.5
    cx = lsb + r
    bot = stroke(system, oval_points(cx, r, r, r, n=12), closed=True, thickness=st * 0.85)
    top = stroke(system, oval_points(cx, xh * 0.62, r, r, n=12), closed=True, thickness=st * 0.85)
    return bot + top

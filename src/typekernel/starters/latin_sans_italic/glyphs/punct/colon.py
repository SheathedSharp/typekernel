"""colon — two stacked thin dots (G-class)."""

from __future__ import annotations

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System

_DOT_N = 16


@glyph("colon", group="punct")
def colon(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    r = st * 0.55
    lsb = float(system.tokens["lsb_lc"]) * 0.5
    cx = lsb + r
    bot = stroke(system, oval_points(cx, r, r, r, n=_DOT_N), closed=True, thickness=st * 0.4)
    top = stroke(
        system, oval_points(cx, xh * 0.62, r, r, n=_DOT_N), closed=True, thickness=st * 0.4
    )
    return bot + top

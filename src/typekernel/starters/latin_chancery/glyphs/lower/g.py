"""g — upper oval + gapped descender (interpolation-safe; dual bowl self-intersection)."""

from __future__ import annotations

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System

_OVAL_N = 48
_GAP = 70.0


@glyph("g", group="lc.round")
def g(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    desc = float(system.zones.desc)
    width = float(system.tokens.get("g_width", 420.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    cy = xh / 2.0
    rx = width / 2.0 - st * 0.15
    ry = xh / 2.0 + ov * 0.35 - st * 0.1
    bowl = stroke(system, oval_points(cx, cy, rx, ry, n=_OVAL_N), closed=True, thickness=st)
    x = lsb + width - st * 0.45
    y0 = min(cy - ry - _GAP, -10.0)
    return bowl + stroke(system, [(x, y0), (x, desc)], thickness=st)

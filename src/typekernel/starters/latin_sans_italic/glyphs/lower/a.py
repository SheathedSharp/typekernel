"""o-group a — stem + gapped oval ."""

from __future__ import annotations

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System

_OVAL_N = 48
_GAP = 60.0


@glyph("a", group="lc.bowl")
def a(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("o_width", 470.0)) * 0.95
    lsb = float(system.tokens["lsb_lc"])
    x_stem = lsb + width - st * 0.5
    stem_d = stroke(system, [(x_stem, 0.0), (x_stem, xh)], thickness=st)
    gap = _GAP
    rx = (width - st) * 0.36
    ry = xh * 0.40
    cx = x_stem - st * 0.5 - gap - rx
    cy = xh / 2.0
    bowl = stroke(
        system, oval_points(cx, cy, rx, ry, n=_OVAL_N), closed=True, thickness=st
    )
    return stem_d + bowl

"""exclam — stem + thin period (G-class)."""

from __future__ import annotations

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System

_DOT_N = 16


@glyph("exclam", group="punct")
def exclam(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    lsb = float(system.tokens["lsb_lc"]) * 0.6
    x = lsb + st * 0.5
    stem = stroke(system, [(x, st * 2.2), (x, xh)], thickness=st)
    r = st * 0.55
    dot = stroke(system, oval_points(x, r, r, r, n=_DOT_N), closed=True, thickness=st * 0.4)
    return stem + dot

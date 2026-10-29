"""n-group glyph i — stem + oval tittle (G-class clean)."""

from __future__ import annotations

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("i", group="lc.straight")
def i(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    x = lsb + st * 0.5
    stem = stroke(system, [(x, 0.0), (x, xh * 0.65)], thickness=st)
    cy = xh * 0.88
    pts = oval_points(x, cy, st * 0.35, st * 0.4, n=12)
    dot = stroke(system, pts, closed=True, thickness=st * 0.35)
    return stem + dot

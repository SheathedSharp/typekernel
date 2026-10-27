"""quotedbl — two short vertical marks (skeleton+pen)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("quotedbl", group="punct")
def quotedbl(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    lsb = float(system.tokens.get("lsb_lc", 36.0)) * 0.45
    y0, y1 = xh * 0.72, xh + st * 0.15
    left = stroke(system, [(lsb + st * 0.35, y0), (lsb + st * 0.35, y1)], thickness=st * 0.8)
    right = stroke(system, [(lsb + st * 1.35, y0), (lsb + st * 1.35, y1)], thickness=st * 0.8)
    return left + right

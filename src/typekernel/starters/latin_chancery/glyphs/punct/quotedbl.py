"""quotedbl — two short verticals."""
from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("quotedbl", group="punct")
def quotedbl(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    asc = float(system.zones.asc)
    lsb = float(system.tokens.get("lsb_lc", 32.0)) * 0.5
    gap = st * 1.4
    x0 = lsb + st * 0.4
    y0, y1 = xh * 0.85, asc - 20.0
    return stroke(system, [(x0, y0), (x0, y1)], thickness=st * 0.85) + stroke(
        system, [(x0 + gap, y0), (x0 + gap, y1)], thickness=st * 0.85
    )

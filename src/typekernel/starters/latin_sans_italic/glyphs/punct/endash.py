"""endash — longer mid-height bar."""

from __future__ import annotations

from elements import WIDTHS, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("endash", group="punct")
def endash(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(WIDTHS.get("endash", 400.0))
    lsb = float(system.tokens["lsb_lc"]) * 0.5
    y = xh * 0.42
    return stroke(system, [(lsb, y), (lsb + width, y)], thickness=st * 0.85)

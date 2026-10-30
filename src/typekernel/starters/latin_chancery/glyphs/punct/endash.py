"""endash — longer mid-height bar (skeleton+pen)."""
from __future__ import annotations

from elements import WIDTHS, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("endash", group="punct")
def endash(system: System):
    st = float(system.stem["lc_h"])
    xh = float(system.zones.x)
    width = float(WIDTHS.get("endash", 400.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0)) * 0.5
    y = xh * 0.48
    return stroke(system, [(lsb, y), (lsb + width, y)], thickness=st)

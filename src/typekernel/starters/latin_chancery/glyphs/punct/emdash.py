"""emdash — longest mid-height bar (skeleton+pen)."""
from __future__ import annotations

from elements import WIDTHS, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("emdash", group="punct")
def emdash(system: System):
    st = float(system.stem["lc_h"])
    xh = float(system.zones.x)
    width = float(WIDTHS.get("emdash", 800.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0)) * 0.4
    y = xh * 0.48
    return stroke(system, [(lsb, y), (lsb + width, y)], thickness=st)

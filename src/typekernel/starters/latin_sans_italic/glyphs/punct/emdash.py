"""emdash — longest mid-height bar."""

from __future__ import annotations

from elements import WIDTHS, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("emdash", group="punct")
def emdash(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(WIDTHS.get("emdash", 800.0))
    lsb = float(system.tokens["lsb_lc"]) * 0.4
    y = xh * 0.42
    return stroke(system, [(lsb, y), (lsb + width, y)], thickness=st * 0.85)

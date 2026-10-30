"""slash — diagonal."""

from __future__ import annotations

from elements import WIDTHS, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("slash", group="punct")
def slash(system: System):
    st = float(system.stem["lc"])
    asc = float(system.zones.asc)
    desc = float(system.zones.desc) * 0.4
    width = float(WIDTHS.get("slash", 280.0))
    lsb = float(system.tokens["lsb_lc"])
    return stroke(system, [(lsb, desc), (lsb + width, asc)], thickness=st * 0.9)

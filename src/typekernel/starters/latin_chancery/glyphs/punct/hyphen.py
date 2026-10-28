"""hyphen — mid bar."""
from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("hyphen", group="punct")
def hyphen(system: System):
    st = float(system.stem["lc_h"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("hyphen_width", 220.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0)) * 0.5
    y = xh * 0.48
    return stroke(system, [(lsb, y), (lsb + width, y)], thickness=st)

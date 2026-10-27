"""hyphen — mid-height bar (skeleton+pen)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("hyphen", group="punct")
def hyphen(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("hyphen_width", 200.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0)) * 0.6
    y = xh * 0.42
    return stroke(system, [(lsb, y), (lsb + width, y)], thickness=st * 0.85)

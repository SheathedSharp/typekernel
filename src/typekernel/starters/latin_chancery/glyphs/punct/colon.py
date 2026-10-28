"""colon — two pen_dots."""
from __future__ import annotations

from elements import pen_dot

from typekernel.project import glyph
from typekernel.system import System


@glyph("colon", group="punct")
def colon(system: System):
    r = float(system.stem.get("lc_h", system.stem["lc"])) * (
        float(system.tokens.get("dot_radius", 28.0)) / 36.0
    )
    xh = float(system.zones.x)
    lsb = float(system.tokens.get("lsb_lc", 32.0)) * 0.5
    cx = lsb + r
    return pen_dot(system, cx, r * 0.9) + pen_dot(system, cx, xh - r * 0.9)

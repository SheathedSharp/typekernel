"""parenleft — open arc (skeleton+pen)."""

from __future__ import annotations

from elements import open_arc_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("parenleft", group="punct")
def parenleft(system: System):
    st = float(system.stem["lc"])
    asc = float(system.zones.asc)
    desc = float(system.zones.desc)
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    h = asc - desc
    cy = (asc + desc) / 2.0
    pts = open_arc_points(lsb + st * 2.2, cy, st * 1.8, h * 0.48, start_deg=70.0, end_deg=290.0, n=18)
    return stroke(system, pts, thickness=st * 0.9)

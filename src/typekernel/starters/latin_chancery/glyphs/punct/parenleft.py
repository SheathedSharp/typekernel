"""parenleft — open arc."""
from __future__ import annotations

from elements import open_arc_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("parenleft", group="punct")
def parenleft(system: System):
    st = float(system.stem["lc"])
    asc = float(system.zones.asc)
    desc = float(system.zones.desc)
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    h = asc - desc
    cy = (asc + desc) / 2.0
    pts = open_arc_points(lsb + 80.0, cy, 70.0, h * 0.48, start_deg=70, end_deg=290, n=28)
    return stroke(system, pts, thickness=st)

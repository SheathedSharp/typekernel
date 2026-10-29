"""parenleft — vertical stem (interpolation-safe; curved arc self-intersection)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("parenleft", group="punct")
def parenleft(system: System):
    st = float(system.stem["lc"])
    asc = float(system.zones.asc)
    desc = float(system.zones.desc)
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    x = lsb + st * 1.2
    return stroke(system, [(x, desc + st), (x, asc - st)], thickness=st * 0.85)

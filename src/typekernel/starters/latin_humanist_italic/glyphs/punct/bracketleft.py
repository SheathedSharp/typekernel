"""bracketleft — vertical with top/bottom bars (skeleton+pen)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("bracketleft", group="punct")
def bracketleft(system: System):
    st = float(system.stem["lc"])
    asc = float(system.zones.asc)
    desc = float(system.zones.desc) * 0.35
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    x = lsb + st * 0.5
    w = st * 1.6
    return (
        stroke(system, [(x, desc), (x, asc)], thickness=st * 0.85)
        + stroke(system, [(x, asc), (x + w, asc)], thickness=st * 0.85)
        + stroke(system, [(x, desc), (x + w, desc)], thickness=st * 0.85)
    )

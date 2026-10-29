"""bracketright — vertical with top/bottom bars (G-class)."""

from __future__ import annotations

from elements import fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("bracketright", group="punct")
def bracketright(system: System):
    st = float(system.stem["lc"])
    asc = float(system.zones.asc)
    desc = float(system.zones.desc) * 0.35
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    w = st * 1.6
    x = lsb + w
    return fuse(
        stroke(system, [(x, desc), (x, asc)], thickness=st * 0.85)
        + stroke(system, [(x, asc), (x - w, asc)], thickness=st * 0.85)
        + stroke(system, [(x, desc), (x - w, desc)], thickness=st * 0.85)
    )

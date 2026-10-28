"""bracketright — vertical with top/bottom bars (skeleton+pen)."""
from __future__ import annotations
from elements import stroke
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
    th = st * 0.85
    return (
        stroke(system, [(x, desc), (x, asc)], thickness=th)
        + stroke(system, [(x, asc), (x - w, asc)], thickness=th)
        + stroke(system, [(x, desc), (x - w, desc)], thickness=th)
    )

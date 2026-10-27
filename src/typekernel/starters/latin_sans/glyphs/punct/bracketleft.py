"""bracketleft — [ shape."""

from __future__ import annotations

from elements import stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("bracketleft", group="punct")
def bracketleft(system: System):
    st = float(system.stem["lc"])
    asc = float(system.zones.asc)
    desc = float(system.zones.desc)
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.45
    arm = st * 1.6
    vert = stem_rect(lsb, lsb + st, desc + st, asc, prefix="vert")
    top = stem_rect(lsb, lsb + arm, asc - st, asc, prefix="top")
    bot = stem_rect(lsb, lsb + arm, desc + st, desc + 2 * st, prefix="bot")
    return vert + top + bot

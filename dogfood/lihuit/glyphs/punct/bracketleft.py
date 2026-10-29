"""bracketleft — anatomy stems (P3-7)."""

from __future__ import annotations

from typekernel.anatomy import crossbar, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("bracketleft", group="punct")
def bracketleft(system: System):
    st = float(system.stem["lc"])
    asc = float(system.zones.asc)
    desc = float(system.zones.desc)
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.45
    arm = st * 1.6
    vert = stem(lsb, lsb + st, desc + st, asc, name="stem")
    top = crossbar(lsb, lsb + arm, asc - st / 2.0, thick=st, name="bar.t", ends="none")
    bot = crossbar(
        lsb, lsb + arm, desc + st * 1.5, thick=st, name="bar.b", ends="none"
    )
    return vert + top + bot

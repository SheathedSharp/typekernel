"""slash — diagonal."""
from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("slash", group="punct", traits=("punct", "no-stem"))
def slash(system: System):
    st = float(system.stem["lc"])
    asc = float(system.zones.asc)
    desc = float(system.zones.desc)
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    return stroke(system, [(lsb + 20.0, desc + 20.0), (lsb + 180.0, asc - 20.0)], thickness=st)

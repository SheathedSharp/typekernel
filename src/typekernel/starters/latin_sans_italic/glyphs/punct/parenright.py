"""parenright — vertical stem (interpolation-safe; curved arc self-intersection under slant)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("parenright", group="punct")
def parenright(system: System):
    st = float(system.stem["lc"])
    asc = float(system.zones.asc)
    desc = float(system.zones.desc)
    lsb = float(system.tokens["lsb_lc"])
    x = lsb + st * 0.8
    return stroke(system, [(x, desc + st), (x, asc - st)], thickness=st * 0.85)

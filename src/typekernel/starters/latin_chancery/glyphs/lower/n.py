"""Control glyph n — slanted stem + arch (chancery pen)."""
from __future__ import annotations

from elements import n_arch_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("n", group="control")
def n(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens["n_width"])
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    rise = float(system.tokens.get("arch_rise", 0.14)) * xh
    x0 = lsb + st * 0.5
    x1 = lsb + width - st * 0.5
    return stroke(system, n_arch_points(x0, x1, 0.0, xh, rise=rise), thickness=st)

"""Lowercase m — double arch."""
from __future__ import annotations

from elements import n_arch_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("m", group="lc.straight")
def m(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("m_width", 620.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    rise = float(system.tokens.get("arch_rise", 0.14)) * xh
    x0 = lsb + st * 0.5
    x2 = lsb + width - st * 0.5
    x1 = (x0 + x2) / 2.0
    return stroke(system, n_arch_points(x0, x1, 0.0, xh, rise=rise), thickness=st) + stroke(
        system, n_arch_points(x1, x2, 0.0, xh, rise=rise), thickness=st
    )

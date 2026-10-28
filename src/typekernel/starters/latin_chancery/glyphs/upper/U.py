"""Uppercase U — u-arch at cap height."""
from __future__ import annotations
from elements import stroke, u_arch_points
from typekernel.project import glyph
from typekernel.system import System

@glyph("U", group="uc.straight")
def U(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("U_width", 560.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    rise = float(system.tokens.get("arch_rise", 0.14)) * cap * 0.6
    x0 = lsb + uc * 0.5
    x1 = lsb + width - uc * 0.5
    return stroke(system, u_arch_points(x0, x1, cap, rise=rise), thickness=uc)

"""Lowercase r — stem + short shoulder."""
from __future__ import annotations
from elements import stroke
from typekernel.project import glyph
from typekernel.system import System

@glyph("r", group="lc.straight")
def r(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("r_width", 240.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    rise = float(system.tokens.get("arch_rise", 0.14)) * xh
    x0 = lsb + st * 0.5
    x1 = lsb + width - st * 0.2
    points = [
        (x0, 0.0),
        (x0, xh - rise),
        (x0 + (x1 - x0) * 0.35, xh),
        (x1, xh - rise * 0.4),
    ]
    return stroke(system, points, thickness=st)

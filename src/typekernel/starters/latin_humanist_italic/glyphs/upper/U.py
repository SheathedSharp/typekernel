"""U — arched capital (skeleton+pen)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("U", group="uc.straight")
def U(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("U_width", 600.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    rise = float(system.tokens.get("arch_rise", 0.12)) * cap * 0.5
    x0 = lsb + uc * 0.5
    x1 = lsb + width - uc * 0.5
    mid = (x0 + x1) / 2.0
    points = [
        (x0, cap),
        (x0, rise * 1.5),
        (x0 + (x1 - x0) * 0.15, 0.0),
        (mid, -rise * 0.2),
        (x1 - (x1 - x0) * 0.15, 0.0),
        (x1, rise * 1.5),
        (x1, cap),
    ]
    return stroke(system, points, thickness=uc)

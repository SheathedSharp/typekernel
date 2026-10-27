"""J — stem with bottom hook (skeleton+pen)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("J", group="uc.straight")
def J(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("J_width", 460.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    x = lsb + width - uc * 0.5
    points = [
        (x, cap),
        (x, uc * 1.2),
        (x - width * 0.25, 0.0),
        (lsb + uc * 0.3, uc * 0.4),
    ]
    return stroke(system, points, thickness=uc)

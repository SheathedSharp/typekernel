"""F — stem + two bars (skeleton+pen)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("F", group="uc.straight")
def F(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("F_width", 460.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    x = lsb + uc * 0.5
    stem = stroke(system, [(x, 0.0), (x, cap)], thickness=uc)
    top = stroke(system, [(x, cap), (lsb + width, cap)], thickness=uc * 0.9)
    mid = stroke(system, [(x, cap * 0.52), (lsb + width * 0.82, cap * 0.52)], thickness=uc * 0.85)
    return stem + top + mid

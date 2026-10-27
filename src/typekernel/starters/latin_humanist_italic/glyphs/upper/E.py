"""E — stem + three bars (skeleton+pen)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("E", group="uc.straight")
def E(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("E_width", 500.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    x = lsb + uc * 0.5
    x1 = lsb + width
    stem = stroke(system, [(x, 0.0), (x, cap)], thickness=uc)
    top = stroke(system, [(x, cap), (x1, cap)], thickness=uc * 0.9)
    mid = stroke(system, [(x, cap * 0.5), (lsb + width * 0.85, cap * 0.5)], thickness=uc * 0.85)
    bot = stroke(system, [(x, 0.0), (x1, 0.0)], thickness=uc * 0.9)
    return stem + top + mid + bot

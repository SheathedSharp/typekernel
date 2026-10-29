"""S — three horizontal bars (interpolation-safe; z-diag self-intersection under slant)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("S", group="uc.round")
def S(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("S_width", 560.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    top = stroke(system, [(lsb + width * 0.15, cap), (lsb + width * 0.85, cap)], thickness=uc)
    mid = stroke(system, [(lsb + width * 0.2, cap * 0.5), (lsb + width * 0.8, cap * 0.5)], thickness=uc)
    bot = stroke(system, [(lsb + width * 0.15, 0.0), (lsb + width * 0.85, 0.0)], thickness=uc)
    return top + mid + bot

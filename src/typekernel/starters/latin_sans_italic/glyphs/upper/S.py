"""S — gapped top/diag/base (P5-3)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System

_GAP = 70.0


@glyph("S", group="uc.round")
def S(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("S_width", 560.0))
    lsb = float(system.tokens["lsb_uc"])
    gap = _GAP
    top = stroke(system, [(lsb + width * 0.15, cap), (lsb + width * 0.85, cap)], thickness=uc)
    diag = stroke(
        system, [(lsb + width * 0.8, cap - gap), (lsb + width * 0.2, gap)], thickness=uc
    )
    bot = stroke(system, [(lsb + width * 0.15, 0.0), (lsb + width * 0.85, 0.0)], thickness=uc)
    return top + diag + bot

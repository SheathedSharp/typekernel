"""C — open bracket with corner gaps (P5-3)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System

_GAP = 70.0


@glyph("C", group="uc.round")
def C(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("O_width", 700.0)) * 0.95
    lsb = float(system.tokens["lsb_uc"])
    gap = _GAP
    x = lsb + width * 0.28
    stem = stroke(system, [(x, uc * 0.3 + gap), (x, cap - uc * 0.3 - gap)], thickness=uc)
    top = stroke(
        system,
        [(x + gap * 0.5, cap - uc * 0.25), (lsb + width * 0.85, cap - uc * 0.25)],
        thickness=uc,
    )
    bot = stroke(
        system,
        [(x + gap * 0.5, uc * 0.25), (lsb + width * 0.85, uc * 0.25)],
        thickness=uc,
    )
    return stem + top + bot

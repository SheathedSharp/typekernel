"""G — open C + right spur (interpolation-safe)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System

_GAP = 70.0


@glyph("G", group="uc.round")
def G(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("G_width", 640.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    gap = _GAP
    x = lsb + width * 0.28
    body = (
        stroke(system, [(x, uc * 0.3 + gap), (x, cap - uc * 0.3 - gap)], thickness=uc)
        + stroke(
            system,
            [(x + gap * 0.5, cap - uc * 0.25), (lsb + width * 0.85, cap - uc * 0.25)],
            thickness=uc,
        )
        + stroke(
            system,
            [(x + gap * 0.5, uc * 0.25), (lsb + width * 0.7, uc * 0.25)],
            thickness=uc,
        )
    )
    spur = stroke(
        system, [(lsb + width * 0.85, uc * 0.25), (lsb + width * 0.85, cap * 0.42)], thickness=uc
    )
    return body + spur

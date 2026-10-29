"""P — stem + gapped upper oval (P5-3)."""

from __future__ import annotations

from elements import oval_points, stroke, uc_stem

from typekernel.project import glyph
from typekernel.system import System

_OVAL_N = 32
_GAP = 60.0


@glyph("P", group="uc.round")
def P(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("P_width", 540.0))
    lsb = float(system.tokens["lsb_uc"])
    x0 = lsb + uc * 0.5
    stem = uc_stem(system, x0, thickness=uc)
    gap = _GAP
    rx = width * 0.30
    cy = cap * 0.68
    ry = cap * 0.20
    bowl = stroke(
        system,
        oval_points(x0 + uc * 0.5 + gap + rx, cy, rx, ry, n=_OVAL_N),
        closed=True,
        thickness=uc * 0.85,
    )
    return stem + bowl

"""R — stem + gapped bowl + leg (G-class)."""

from __future__ import annotations

from elements import oval_points, stroke, uc_stem

from typekernel.project import glyph
from typekernel.system import System

_OVAL_N = 32
_GAP = 60.0


@glyph("R", group="uc.round")
def R(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("R_width", 580.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    x0 = lsb + uc * 0.5
    stem = uc_stem(system, x0, thickness=uc)
    gap = _GAP
    rx = width * 0.28
    cy = cap * 0.70
    ry = cap * 0.18
    bowl = stroke(
        system,
        oval_points(x0 + uc * 0.5 + gap + rx, cy, rx, ry, n=_OVAL_N),
        closed=True,
        thickness=uc * 0.85,
    )
    leg = stroke(
        system,
        [(x0 + gap + uc, cy - ry - gap), (lsb + width - uc * 0.2, 0.0)],
        thickness=uc,
    )
    return stem + bowl + leg

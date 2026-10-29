"""D — stem + gapped oval (interpolation-safe)."""

from __future__ import annotations

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System

_OVAL_N = 48
_GAP = 70.0


@glyph("D", group="uc.round")
def D(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("D_width", 600.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    ov = float(system.overshoot.round)
    x0 = lsb + uc * 0.5
    stem = stroke(system, [(x0, 0.0), (x0, cap)], thickness=uc)
    gap = _GAP
    rx = width * 0.38
    ry = cap / 2.0 + ov * 0.3 - uc * 0.1
    cx = x0 + uc * 0.5 + gap + rx
    cy = cap / 2.0
    bowl = stroke(
        system, oval_points(cx, cy, rx, ry, n=_OVAL_N), closed=True, thickness=uc
    )
    return stem + bowl

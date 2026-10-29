"""Q — O + gapped tail (interpolation-safe; gap ≥70 under slant expand)."""

from __future__ import annotations

import math

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System

_OVAL_N = 48
_GAP = 75.0


@glyph("Q", group="uc.round")
def Q(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("O_width", 700.0))
    lsb = float(system.tokens["lsb_uc"])
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    cy = cap / 2.0
    rx = width / 2.0 - uc * 0.12
    ry = cap / 2.0 + ov - uc * 0.12
    bowl = stroke(
        system, oval_points(cx, cy, rx, ry, n=_OVAL_N), closed=True, thickness=uc
    )
    gap = _GAP
    ang = math.radians(-45.0)
    x0 = cx + (rx + gap) * math.cos(ang)
    y0 = cy + (ry + gap) * math.sin(ang)
    tail = stroke(
        system, [(x0, y0), (cx + rx * 1.2, -uc * 0.2)], thickness=uc * 0.9
    )
    return bowl + tail

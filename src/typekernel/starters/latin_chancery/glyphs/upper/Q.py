"""Q — O + far stub tail (interpolation-safe; near-tail self-intersection under chancery pen)."""

from __future__ import annotations

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System

_OVAL_N = 48


@glyph("Q", group="uc.round")
def Q(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("O_width", 620.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    cy = cap / 2.0
    rx = width / 2.0 - uc * 0.12
    ry = cap / 2.0 + ov - uc * 0.12
    bowl = stroke(system, oval_points(cx, cy, rx, ry, n=_OVAL_N), closed=True, thickness=uc)
    stub = stroke(
        system, [(cx + rx + 80.0, cy - ry * 0.3), (cx + rx + 180.0, cy - ry * 0.5)], thickness=uc * 0.9
    )
    return bowl + stub

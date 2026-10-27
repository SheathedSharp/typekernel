"""Q — O plus tail (skeleton+pen)."""

from __future__ import annotations

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("Q", group="uc.round")
def Q(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("O_width", 620.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    cy = cap / 2.0
    rx = width / 2.0 - uc * 0.12
    ry = cap / 2.0 + ov - uc * 0.12
    bowl = stroke(system, oval_points(cx, cy, rx, ry), closed=True, thickness=uc)
    tail = stroke(
        system,
        [(cx + rx * 0.35, cy - ry * 0.35), (cx + rx * 1.05, -uc * 0.15)],
        thickness=uc,
    )
    return bowl + tail

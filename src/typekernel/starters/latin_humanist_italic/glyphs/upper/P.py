"""P — stem + upper bowl (skeleton+pen)."""

from __future__ import annotations

from elements import open_arc_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("P", group="uc.round")
def P(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("P_width", 520.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    x0 = lsb + uc * 0.5
    stem = stroke(system, [(x0, 0.0), (x0, cap)], thickness=uc)
    cx = lsb + width * 0.42
    cy = cap * 0.68
    rx = width * 0.48
    ry = cap * 0.28
    bowl = stroke(
        system,
        open_arc_points(cx, cy, rx, ry, start_deg=90.0, end_deg=-90.0, n=18),
        thickness=uc,
    )
    return stem + bowl

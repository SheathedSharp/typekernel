"""R — stem + upper bowl + leg (skeleton+pen)."""

from __future__ import annotations

from elements import open_arc_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("R", group="uc.round")
def R(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("R_width", 580.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    x0 = lsb + uc * 0.5
    stem = stroke(system, [(x0, 0.0), (x0, cap)], thickness=uc)
    cx = lsb + width * 0.40
    cy = cap * 0.68
    rx = width * 0.45
    ry = cap * 0.28
    bowl = stroke(
        system,
        open_arc_points(cx, cy, rx, ry, start_deg=90.0, end_deg=-90.0, n=18),
        thickness=uc,
    )
    join_y = cy - ry
    leg = stroke(
        system,
        [(cx + rx * 0.2, join_y), (lsb + width - uc * 0.2, 0.0)],
        thickness=uc,
    )
    return stem + bowl + leg

"""B — stem + two bowls (skeleton+pen)."""

from __future__ import annotations

from elements import open_arc_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("B", group="uc.round")
def B(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("B_width", 560.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    x0 = lsb + uc * 0.5
    stem = stroke(system, [(x0, 0.0), (x0, cap)], thickness=uc)
    cx = lsb + width * 0.42
    rx = width * 0.48
    # Upper bowl
    cy_u = cap * 0.72
    ry_u = cap * 0.26
    upper = stroke(
        system,
        open_arc_points(cx, cy_u, rx * 0.9, ry_u, start_deg=90.0, end_deg=-90.0, n=16),
        thickness=uc,
    )
    cy_l = cap * 0.28
    ry_l = cap * 0.30
    lower = stroke(
        system,
        open_arc_points(cx, cy_l, rx, ry_l, start_deg=90.0, end_deg=-90.0, n=16),
        thickness=uc,
    )
    return stem + upper + lower

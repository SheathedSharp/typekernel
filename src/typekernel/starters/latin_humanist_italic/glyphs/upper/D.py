"""D — stem + right bowl arc (skeleton+pen)."""

from __future__ import annotations

from elements import open_arc_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("D", group="uc.round")
def D(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("D_width", 600.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    ov = float(system.overshoot.round)
    x0 = lsb + uc * 0.5
    stem = stroke(system, [(x0, 0.0), (x0, cap)], thickness=uc)
    cx = lsb + width * 0.42
    cy = cap / 2.0
    rx = width * 0.52
    ry = cap / 2.0 + ov * 0.4
    # Right half bowl from top of stem to bottom.
    arc = stroke(
        system,
        open_arc_points(cx, cy, rx, ry, start_deg=90.0, end_deg=-90.0, n=22),
        thickness=uc,
    )
    return stem + arc

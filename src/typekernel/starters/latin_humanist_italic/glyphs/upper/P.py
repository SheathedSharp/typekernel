"""P — stem + bowl arc nestled into the stem."""

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
    ov = float(system.overshoot.round)
    x0 = lsb + uc * 0.5
    stem = stroke(system, [(x0, 0.0), (x0, cap)], thickness=uc)
    rx = width * 0.42
    cy = cap * 0.68
    ry = cap * 0.28 + ov * 0.25
    pull = 0.38
    arc = open_arc_points(
        x0 + rx * pull, cy, rx, ry, start_deg=125.0, end_deg=-125.0, n=22
    )
    return stem + stroke(system, arc, thickness=uc)

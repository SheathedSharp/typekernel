"""R — stem + continuous bowl arc into diagonal leg."""

from __future__ import annotations

from elements import open_arc_points, stroke, uc_stem

from typekernel.project import glyph
from typekernel.system import System


@glyph("R", group="uc.round")
def R(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("R_width", 580.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    ov = float(system.overshoot.round)
    x0 = lsb + uc * 0.5
    rx = width * 0.40
    cy = cap * 0.68
    ry = cap * 0.28 + ov * 0.25
    pull = 0.38
    arc = open_arc_points(
        x0 + rx * pull, cy, rx, ry, start_deg=125.0, end_deg=-125.0, n=22
    )
    # Continuous: bowl terminals share stem ink; leg continues from lower terminal.
    leg_tip = (lsb + width - uc * 0.15, 0.0)
    bowl_leg = stroke(system, list(arc) + [leg_tip], thickness=uc)
    return uc_stem(system, x0, thickness=uc) + bowl_leg

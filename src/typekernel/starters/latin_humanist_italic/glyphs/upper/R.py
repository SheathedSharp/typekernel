"""R — stem + nestled bowl arc + leg from lower terminal."""

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
    ov = float(system.overshoot.round)
    x0 = lsb + uc * 0.5
    stem = stroke(system, [(x0, 0.0), (x0, cap)], thickness=uc)
    rx = width * 0.40
    cy = cap * 0.68
    ry = cap * 0.28 + ov * 0.25
    pull = 0.38
    arc = open_arc_points(
        x0 + rx * pull, cy, rx, ry, start_deg=125.0, end_deg=-125.0, n=22
    )
    bowl = stroke(system, arc, thickness=uc)
    # Leg from lower bowl terminal toward baseline-right.
    join = arc[len(arc) // 2]  # east belly — too far; use lower terminal
    join = arc[-1]
    # Nudge join slightly off the stem into the bowl before dropping the leg.
    leg = stroke(
        system,
        [
            (join[0] + rx * 0.15, join[1]),
            (lsb + width - uc * 0.15, 0.0),
        ],
        thickness=uc,
    )
    return stem + bowl + leg

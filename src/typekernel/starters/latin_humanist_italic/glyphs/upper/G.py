"""G — open oval + spur bar (skeleton+pen)."""

from __future__ import annotations

from elements import open_arc_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("G", group="uc.round")
def G(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("G_width", 640.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    cy = cap / 2.0
    rx = width / 2.0 - uc * 0.1
    ry = cap / 2.0 + ov - uc * 0.1
    bowl = stroke(
        system,
        open_arc_points(cx, cy, rx, ry, start_deg=30.0, end_deg=330.0, n=28),
        thickness=uc,
    )
    # Spur: vertical stub + inward bar at mid-right.
    sx = cx + rx * 0.92
    spur = stroke(system, [(sx, cy), (sx, cy - uc * 0.1), (cx + rx * 0.15, cy)], thickness=uc * 0.9)
    return bowl + spur

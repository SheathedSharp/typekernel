"""Uppercase J — stem into fixed open-arc hook (VF-stable polyline)."""
from __future__ import annotations
from elements import open_arc_points, stroke
from typekernel.project import glyph
from typekernel.system import System

@glyph("J", group="uc.straight")
def J(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    width = float(system.tokens.get("J_width", 360.0))
    x = lsb + width - uc * 0.5
    stem = stroke(system, [(x, cap), (x, uc * 1.4)], thickness=uc)
    # Fixed-n open arc hook (no cubic flourish → densify/degen stays stable).
    cx, cy = x - 70.0, uc * 0.9
    hook = stroke(
        system,
        open_arc_points(cx, cy, 85.0, 70.0, start_deg=10, end_deg=200, n=24),
        thickness=float(system.stem["uc_h"]),
    )
    return stem + hook

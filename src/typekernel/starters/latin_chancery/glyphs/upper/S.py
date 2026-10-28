"""Uppercase S — stacked open bowls."""
from __future__ import annotations
from elements import open_bowl
from typekernel.project import glyph
from typekernel.system import System

@glyph("S", group="uc.round")
def S(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("S_width", 480.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    rx = width / 2.0 * 0.95
    overlap = uc * 0.85
    ry = max(cap * 0.28, (cap + 2.0 * ov + overlap) / 4.0)
    upper = open_bowl(
        system, cx=cx, cy=(cap + ov) - ry, rx=rx, ry=ry, thickness=uc,
        open_side="right", aperture_deg=70.0,
    )
    lower = open_bowl(
        system, cx=cx, cy=(-ov) + ry, rx=rx, ry=ry, thickness=uc,
        open_side="left", aperture_deg=70.0,
    )
    return upper + lower

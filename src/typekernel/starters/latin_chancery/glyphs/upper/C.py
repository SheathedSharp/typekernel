"""Uppercase C — open bowl."""
from __future__ import annotations
from elements import open_bowl
from typekernel.project import glyph
from typekernel.system import System

@glyph("C", group="uc.round")
def C(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("O_width", 580.0)) * 0.95
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    ov = float(system.overshoot.round)
    return open_bowl(
        system,
        cx=lsb + width * 0.5,
        cy=cap * 0.5,
        rx=width * 0.5 - uc * 0.1,
        ry=cap * 0.5 + ov * 0.5,
        thickness=uc,
        open_side="right",
        aperture_deg=72.0,
    )

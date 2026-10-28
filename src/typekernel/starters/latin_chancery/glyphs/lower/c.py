"""Lowercase c — open bowl."""
from __future__ import annotations
from elements import open_bowl
from typekernel.project import glyph
from typekernel.system import System

@glyph("c", group="lc.round")
def c(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("o_width", 400.0)) * 0.92
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    ov = float(system.overshoot.round)
    return open_bowl(
        system,
        cx=lsb + width * 0.5,
        cy=xh * 0.5,
        rx=width * 0.5 - st * 0.1,
        ry=xh * 0.5 + ov * 0.5,
        thickness=st,
        open_side="right",
        aperture_deg=78.0,
    )

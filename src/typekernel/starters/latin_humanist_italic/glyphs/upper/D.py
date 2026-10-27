"""D — stem + nestled closed bowl (shared nest_bowl)."""

from __future__ import annotations

from elements import nest_bowl, stroke

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
    bowl = nest_bowl(
        system,
        stem_x=x0,
        side="right",
        width=width,
        xh=cap,
        lsb=lsb,
        thickness=uc,
        cy=cap / 2.0,
        rx=width * 0.44,
        ry=cap / 2.0 + ov * 0.4 - uc * 0.1,
        pull=0.62,
    )
    return stem + bowl

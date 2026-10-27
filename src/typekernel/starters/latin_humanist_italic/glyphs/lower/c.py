"""Round glyph c — open_bowl aperture on the right."""

from __future__ import annotations

from elements import open_bowl

from typekernel.project import glyph
from typekernel.system import System


@glyph("c", group="lc.round")
def c(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("o_width", 420.0)) * 0.95
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    cy = xh / 2.0
    rx = width / 2.0 - st * 0.1
    ry = xh / 2.0 + ov * 0.5 - st * 0.1
    return open_bowl(
        system,
        cx=cx,
        cy=cy,
        rx=rx,
        ry=ry,
        thickness=st,
        open_side="right",
        aperture_deg=80.0,
    )

"""Round glyph c — open_bowl (shared with C/s), aperture on the right."""

from __future__ import annotations

from elements import open_bowl

from typekernel.project import glyph
from typekernel.system import System


@glyph("c", group="lc.round")
def c(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens["c_width"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    cy = xh / 2.0
    rx, ry = width / 2.0, xh / 2.0 + ov
    return open_bowl(
        system,
        cx=cx,
        cy=cy,
        rx=rx,
        ry=ry,
        thickness=st,
        open_side="right",
        tag_prefix="c.aperture",
    )

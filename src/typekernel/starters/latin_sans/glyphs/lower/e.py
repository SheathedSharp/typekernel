"""Round glyph e — bowl with crossbar (counter cut by bar)."""

from __future__ import annotations

from elements import WIDTHS, bowl, crossbar

from typekernel.project import glyph
from typekernel.system import System


@glyph("e", group="lc.round")
def e(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(WIDTHS["e"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    cy = xh / 2.0
    rx = width / 2.0
    ry = xh / 2.0 + ov
    ring = bowl(system, cx=cx, cy=cy, rx=rx, ry=ry, thickness=st)
    # Crossbar through the eye, overlapping left/right of the ring.
    bar_y = xh * 0.55
    bar = crossbar(
        system,
        x0=lsb + st * 0.35,
        x1=lsb + width - st * 0.15,
        cy=bar_y,
        tag_prefix="e.bar",
    )
    return ring + bar

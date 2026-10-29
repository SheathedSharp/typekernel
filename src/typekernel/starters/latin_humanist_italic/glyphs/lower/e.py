"""Round glyph e — open_bowl + crossbar (P5-2; closes A-14 ə/θ)."""

from __future__ import annotations

from elements import open_bowl, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("e", group="lc.round")
def e(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    width = float(system.tokens.get("o_width", 420.0)) * 0.98
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    cy = xh / 2.0
    rx = width / 2.0 - st * 0.1
    ry = xh / 2.0 + ov * 0.5 - st * 0.1
    bowl = open_bowl(
        system,
        cx=cx,
        cy=cy,
        rx=rx,
        ry=ry,
        thickness=st,
        open_side="right",
        aperture_deg=72.0,
    )
    # Crossbar sits on the lower aperture lip; stop short of the opening.
    bar_y = cy - ry * 0.08
    bar = stroke(
        system,
        [(cx - rx * 0.82, bar_y), (cx + rx * 0.42, bar_y)],
        thickness=thin,
    )
    return bowl + bar

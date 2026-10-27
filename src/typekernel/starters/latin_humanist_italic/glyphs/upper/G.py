"""G — open capital bowl + spur bar (shared open_bowl)."""

from __future__ import annotations

from elements import open_bowl, stroke

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
    # Slightly smaller aperture than C so the spur has a longer right stub.
    bowl = open_bowl(
        system,
        cx=cx,
        cy=cy,
        rx=rx,
        ry=ry,
        thickness=uc,
        open_side="right",
        aperture_deg=55.0,
        n=28,
    )
    sx = cx + rx * 0.92
    spur = stroke(
        system,
        [(sx, cy + uc * 0.05), (sx, cy), (cx + rx * 0.15, cy)],
        thickness=uc * 0.9,
    )
    return bowl + spur

"""O-group glyph C — open_bowl at cap height."""

from __future__ import annotations

from elements import open_bowl

from typekernel.project import glyph
from typekernel.system import System


@glyph("C", group="uc.bowl")
def glyph_C(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens["C_width"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    cy = cap / 2.0
    rx, ry = width / 2.0, cap / 2.0 + ov
    return open_bowl(
        system,
        cx=cx,
        cy=cy,
        rx=rx,
        ry=ry,
        thickness=st,
        open_side="right",
        tag_prefix="C.aperture",
    )

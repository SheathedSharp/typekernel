"""O-group glyph G — open_bowl with spur bar (shared C body)."""

from __future__ import annotations

from elements import WIDTHS, crossbar, open_bowl

from typekernel.project import glyph
from typekernel.system import System


@glyph("G", group="uc.bowl")
def glyph_G(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["G"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    cy = cap / 2.0
    rx, ry = width / 2.0, cap / 2.0 + ov
    body = open_bowl(
        system,
        cx=cx,
        cy=cy,
        rx=rx,
        ry=ry,
        thickness=st,
        open_side="right",
        tag_prefix="G.aperture",
    )
    # Spur overlaps the aperture; same crossbar element as E/e.
    bar = crossbar(
        system,
        x0=cx,
        x1=lsb + width - st * 0.15,
        cy=cap * 0.42,
        tag_prefix="G.spur",
    )
    return body + bar

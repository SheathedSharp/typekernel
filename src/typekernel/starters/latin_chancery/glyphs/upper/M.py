"""M — continuous W-like through apexes (G-class)."""

from __future__ import annotations

from elements import fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("M", group="uc.diag")
def M(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("M_width", 780.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + uc * 0.4
    x3 = lsb + width - uc * 0.4
    x1 = lsb + width * 0.38
    x2 = lsb + width * 0.62
    return fuse(
        stroke(
            system,
            [(x0, 0.0), (x0, cap), (x1, cap * 0.35), (x2, cap), (x3, 0.0)],
            thickness=uc,
        )
    )

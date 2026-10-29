"""UC V — two diagonals."""

from __future__ import annotations

from elements import fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("V", group="uc.diag")
def V(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("V_width", 640.0))
    lsb = float(system.tokens["lsb_uc"])
    x0 = lsb + st * 0.3
    x1 = lsb + width - st * 0.3
    mid = (x0 + x1) / 2.0
    return fuse(
        stroke(system, [(x0, cap), (mid, 0.0)], thickness=st)
        + stroke(system, [(x1, cap), (mid, 0.0)], thickness=st)
    )

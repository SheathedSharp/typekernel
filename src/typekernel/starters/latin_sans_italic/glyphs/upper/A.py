"""UC A — diagonals + crossbar."""

from __future__ import annotations

from elements import fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("A", group="uc.diag")
def A(system: System):
    st = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap)
    width = float(system.tokens.get("A_width", 640.0))
    lsb = float(system.tokens["lsb_uc"])
    x0 = lsb + st * 0.3
    x1 = lsb + width - st * 0.3
    mid = (x0 + x1) / 2.0
    bar_y = cap * 0.38
    return fuse(
        stroke(system, [(x0, 0.0), (mid, cap)], thickness=st)
        + stroke(system, [(x1, 0.0), (mid, cap)], thickness=st)
        + stroke(system, [(x0 + (mid - x0) * 0.35, bar_y), (x1 - (x1 - mid) * 0.35, bar_y)], thickness=thin)
    )

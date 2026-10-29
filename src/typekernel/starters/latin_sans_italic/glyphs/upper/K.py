"""UC K — stem + diagonal legs."""

from __future__ import annotations

from elements import fuse, stroke, uc_stem

from typekernel.project import glyph
from typekernel.system import System


@glyph("K", group="uc.diag")
def K(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("K_width", 600.0))
    lsb = float(system.tokens["lsb_uc"])
    x0 = lsb + st * 0.5
    x1 = lsb + width - st * 0.3
    join = cap * 0.48
    return fuse(
        uc_stem(system, x0, thickness=st)
        + stroke(system, [(x0 + st * 0.2, join), (x1, cap)], thickness=st)
        + stroke(system, [(x0 + st * 0.2, join), (x1, 0.0)], thickness=st)
    )

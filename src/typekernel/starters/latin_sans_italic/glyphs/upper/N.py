"""UC N — stems + diagonal."""

from __future__ import annotations

from elements import fuse, stroke, uc_stem

from typekernel.project import glyph
from typekernel.system import System


@glyph("N", group="uc.straight")
def N(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("N_width", 620.0))
    lsb = float(system.tokens["lsb_uc"])
    x0 = lsb + st * 0.5
    x1 = lsb + width - st * 0.5
    return fuse(
        uc_stem(system, x0, thickness=st)
        + uc_stem(system, x1, thickness=st)
        + stroke(system, [(x0, cap), (x1, 0.0)], thickness=st)
    )

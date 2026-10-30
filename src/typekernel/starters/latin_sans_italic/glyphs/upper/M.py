"""UC M — outer stems + inner diagonals."""

from __future__ import annotations

from elements import WIDTHS, fuse, stroke, uc_stem

from typekernel.project import glyph
from typekernel.system import System


@glyph("M", group="uc.straight")
def M(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS.get("M", 780.0))
    lsb = float(system.tokens["lsb_uc"])
    x0 = lsb + st * 0.5
    x1 = lsb + width - st * 0.5
    mid = (x0 + x1) / 2.0
    return fuse(
        uc_stem(system, x0, thickness=st)
        + uc_stem(system, x1, thickness=st)
        + stroke(system, [(x0, cap), (mid, cap * 0.2)], thickness=st)
        + stroke(system, [(x1, cap), (mid, cap * 0.2)], thickness=st)
    )

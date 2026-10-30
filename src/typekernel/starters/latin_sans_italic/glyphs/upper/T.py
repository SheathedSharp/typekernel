"""UC T — stem + top bar."""

from __future__ import annotations

from elements import WIDTHS, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("T", group="uc.straight")
def T(system: System):
    st = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap)
    width = float(WIDTHS.get("T", 560.0))
    lsb = float(system.tokens["lsb_uc"])
    x = lsb + width / 2.0
    stem = stroke(system, [(x, 0.0), (x, cap)], thickness=st)
    bar = stroke(system, [(lsb, cap), (lsb + width, cap)], thickness=thin)
    return stem + bar

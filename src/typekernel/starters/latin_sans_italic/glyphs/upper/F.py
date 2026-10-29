"""UC F — continuous top+stem rail + mid bar (interpolation-safe)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("F", group="uc.straight")
def F(system: System):
    st = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap)
    width = float(system.tokens.get("F_width", 480.0))
    lsb = float(system.tokens["lsb_uc"])
    x = lsb + st * 0.5
    rail = stroke(system, [(lsb + width, cap), (x, cap), (x, 0.0)], thickness=st)
    mid = stroke(system, [(x, cap * 0.5), (lsb + width * 0.8, cap * 0.5)], thickness=thin)
    return rail + mid

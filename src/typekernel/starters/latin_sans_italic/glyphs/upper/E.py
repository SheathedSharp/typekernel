"""UC E — continuous top/stem/bottom rail + mid bar (interpolation-safe)."""

from __future__ import annotations

from elements import fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("E", group="uc.straight")
def E(system: System):
    st = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap)
    width = float(system.tokens.get("E_width", 520.0))
    lsb = float(system.tokens["lsb_uc"])
    x = lsb + st * 0.5
    rail = stroke(system, [(lsb + width, cap), (x, cap), (x, 0.0), (lsb + width, 0.0)], thickness=st)
    mid = stroke(system, [(x, cap * 0.5), (lsb + width * 0.85, cap * 0.5)], thickness=thin)
    return fuse(rail + mid)

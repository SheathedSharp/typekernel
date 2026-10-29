"""UC E — stem + three bars."""

from __future__ import annotations

from elements import stroke, uc_stem

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
    stem = uc_stem(system, x, thickness=st)
    top = stroke(system, [(x, cap), (lsb + width, cap)], thickness=thin)
    mid = stroke(system, [(x, cap * 0.5), (lsb + width * 0.85, cap * 0.5)], thickness=thin)
    bot = stroke(system, [(x, 0.0), (lsb + width, 0.0)], thickness=thin)
    return stem + top + mid + bot

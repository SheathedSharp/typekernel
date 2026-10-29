"""Control H — two stems + bar."""

from __future__ import annotations

from elements import stroke, uc_stem

from typekernel.project import glyph
from typekernel.system import System


@glyph("H", group="control")
def H(system: System):
    st = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", st * 0.85))
    width = float(system.tokens["H_width"])
    lsb = float(system.tokens["lsb_uc"])
    cap = float(system.zones.cap)
    x0 = lsb + st * 0.5
    x1 = lsb + width - st * 0.5
    left = uc_stem(system, x0, thickness=st)
    right = uc_stem(system, x1, thickness=st)
    bar = stroke(system, [(x0, cap * 0.48), (x1, cap * 0.48)], thickness=thin)
    return left + right + bar

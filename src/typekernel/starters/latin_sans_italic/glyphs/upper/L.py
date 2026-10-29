"""UC L — continuous stem + baseline bar (fused for interpolation)."""

from __future__ import annotations

from elements import fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("L", group="uc.straight")
def L(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("L_width", 500.0))
    lsb = float(system.tokens["lsb_uc"])
    x = lsb + st * 0.5
    return fuse(stroke(system, [(x, cap), (x, 0.0), (lsb + width, 0.0)], thickness=st))

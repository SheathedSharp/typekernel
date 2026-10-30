"""T — continuous left-half bar into stem + right bar (shared apex)."""

from __future__ import annotations

from elements import WIDTHS, fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("T", group="uc.straight")
def T(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS.get("T", 560.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    mid = lsb + width / 2.0
    # Left bar → stem is one rail; right bar meets at mid/cap.
    left = stroke(system, [(lsb, cap), (mid, cap), (mid, 0.0)], thickness=uc)
    right = stroke(system, [(mid, cap), (lsb + width, cap)], thickness=uc)
    return fuse(left + right)

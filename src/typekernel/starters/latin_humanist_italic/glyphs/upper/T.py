"""T — top bar + stem (skeleton+pen)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("T", group="uc.straight")
def T(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("T_width", 560.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    mid = lsb + width / 2.0
    bar = stroke(system, [(lsb, cap), (lsb + width, cap)], thickness=uc * 0.9)
    stem = stroke(system, [(mid, 0.0), (mid, cap)], thickness=uc)
    return bar + stem

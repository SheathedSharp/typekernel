"""Uppercase T — crossbar + stem."""
from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("T", group="uc.straight")
def T(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("T_width", 520.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + uc * 0.15
    x1 = lsb + width - uc * 0.15
    mid = (x0 + x1) / 2.0
    bar = stroke(system, [(x0, cap), (x1, cap)], thickness=float(system.stem["uc_h"]))
    stem = stroke(system, [(mid, 0.0), (mid, cap)], thickness=uc)
    return bar + stem

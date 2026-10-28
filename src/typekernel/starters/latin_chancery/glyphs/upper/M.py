"""Uppercase M — four stems / diagonals."""
from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("M", group="uc.straight")
def M(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("M_width", 700.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + uc * 0.5
    x3 = lsb + width - uc * 0.5
    mid = (x0 + x3) / 2.0
    return (
        stroke(system, [(x0, 0.0), (x0, cap)], thickness=uc)
        + stroke(system, [(x0, cap), (mid, cap * 0.35)], thickness=uc)
        + stroke(system, [(mid, cap * 0.35), (x3, cap)], thickness=uc)
        + stroke(system, [(x3, cap), (x3, 0.0)], thickness=uc)
    )

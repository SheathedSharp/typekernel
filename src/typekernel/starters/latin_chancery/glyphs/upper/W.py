"""Uppercase W — double V."""
from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("W", group="uc.diag")
def W(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("W_width", 780.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + uc * 0.15
    x3 = lsb + width - uc * 0.15
    x1 = x0 + (x3 - x0) / 3.0
    x2 = x0 + 2.0 * (x3 - x0) / 3.0
    return (
        stroke(system, [(x0, cap), (x1, 0.0)], thickness=uc)
        + stroke(system, [(x1, 0.0), ((x1 + x2) / 2.0, cap * 0.55)], thickness=uc)
        + stroke(system, [((x1 + x2) / 2.0, cap * 0.55), (x2, 0.0)], thickness=uc)
        + stroke(system, [(x2, 0.0), (x3, cap)], thickness=uc)
    )

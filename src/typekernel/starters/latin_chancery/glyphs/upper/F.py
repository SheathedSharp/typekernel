"""F — continuous top+stem rail + mid bar (interpolation-safe)."""

from __future__ import annotations

from elements import WIDTHS, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("F", group="uc.straight")
def F(system: System):
    uc = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", uc * 0.85))
    cap = float(system.zones.cap)
    width = float(WIDTHS.get("F", 480.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x = lsb + uc * 0.5
    rail = stroke(system, [(lsb + width, cap), (x, cap), (x, 0.0)], thickness=uc)
    mid = stroke(system, [(x, cap * 0.52), (lsb + width * 0.82, cap * 0.52)], thickness=thin)
    return rail + mid

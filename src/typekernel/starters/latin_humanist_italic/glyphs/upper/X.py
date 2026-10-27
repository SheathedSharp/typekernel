"""X — crossing diagonals (skeleton+pen)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("X", group="uc.diag")
def X(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("X_width", 600.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    x0 = lsb + uc * 0.2
    x1 = lsb + width - uc * 0.2
    return (
        stroke(system, [(x0, cap), (x1, 0.0)], thickness=uc)
        + stroke(system, [(x1, cap), (x0, 0.0)], thickness=uc)
    )

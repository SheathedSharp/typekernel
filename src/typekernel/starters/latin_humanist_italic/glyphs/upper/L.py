"""L — continuous stem + baseline bar (fused for interpolation)."""

from __future__ import annotations

from elements import WIDTHS, fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("L", group="uc.straight")
def L(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS.get("L", 480.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    x = lsb + uc * 0.5
    return fuse(
        stroke(
            system,
            [(x, cap), (x, 0.0), (lsb + width, 0.0)],
            thickness=uc,
        )
    )

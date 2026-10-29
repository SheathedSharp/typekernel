"""D — stem + continuous outer rail (interpolation-safe; nest oval self-intersection)."""

from __future__ import annotations

from elements import fuse, stroke, uc_stem

from typekernel.project import glyph
from typekernel.system import System


@glyph("D", group="uc.round")
def D(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("D_width", 620.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + uc * 0.5
    x1 = lsb + width * 0.85
    return fuse(
        uc_stem(system, x0, thickness=uc)
        + stroke(system, [(x0, cap), (x1, cap), (x1, 0.0), (x0, 0.0)], thickness=uc)
    )

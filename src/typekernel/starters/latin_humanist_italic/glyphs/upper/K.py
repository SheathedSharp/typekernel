"""K — shared uc_stem + continuous arm/leg through stem join."""

from __future__ import annotations

from elements import fuse, stroke, uc_stem

from typekernel.project import glyph
from typekernel.system import System


@glyph("K", group="uc.diag")
def K(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("K_width", 580.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    x0 = lsb + uc * 0.5
    x1 = lsb + width - uc * 0.25
    join = cap * 0.45
    # Arms meet exactly on the stem so overlays share ink (no gap spur).
    arms = stroke(system, [(x1, cap), (x0, join), (x1, 0.0)], thickness=uc)
    return fuse(uc_stem(system, x0, thickness=uc) + arms)

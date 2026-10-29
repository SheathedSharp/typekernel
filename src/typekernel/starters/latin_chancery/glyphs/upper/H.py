"""Control glyph H — fused stems + crossbar (interpolation-safe)."""

from __future__ import annotations

from elements import fuse, stroke, uc_stem

from typekernel.project import glyph
from typekernel.system import System


@glyph("H", group="control")
def H(system: System):
    uc = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", uc * 0.85))
    cap = float(system.zones.cap)
    width = float(system.tokens["H_width"])
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + uc * 0.5
    x1 = lsb + width - uc * 0.5
    return fuse(
        uc_stem(system, x0, thickness=uc)
        + uc_stem(system, x1, thickness=uc)
        + stroke(system, [(x0, cap * 0.48), (x1, cap * 0.48)], thickness=thin)
    )

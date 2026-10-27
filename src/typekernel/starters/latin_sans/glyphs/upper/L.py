"""H-group glyph L — stem + baseline bar."""

from __future__ import annotations

from elements import crossbar, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("L", group="uc.straight")
def glyph_L(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens["L_width"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    stem = stem_rect(lsb, lsb + uc, 0.0, cap, prefix="stem.l")
    bar_t = float(system.tokens.get("bar_thickness", uc * 0.85))
    bar = crossbar(
        system, x0=lsb, x1=lsb + width, cy=bar_t / 2.0, tag_prefix="L.bar"
    )
    return stem + bar

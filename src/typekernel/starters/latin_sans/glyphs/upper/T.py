"""H-group glyph T — top bar + centered stem."""

from __future__ import annotations

from elements import crossbar, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("T", group="uc.straight")
def glyph_T(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens["T_width"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    bar_t = float(system.tokens.get("bar_thickness", uc * 0.85))
    x0 = lsb + (width - uc) / 2.0
    stem = stem_rect(x0, x0 + uc, 0.0, cap, prefix="stem")
    bar = crossbar(
        system, x0=lsb, x1=lsb + width, cy=cap - bar_t / 2.0, tag_prefix="T.bar"
    )
    return stem + bar

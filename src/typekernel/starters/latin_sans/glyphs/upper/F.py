"""H-group glyph F — stem + top/mid bars."""

from __future__ import annotations

from elements import WIDTHS, crossbar, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("F", group="uc.straight")
def glyph_F(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["F"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    bar_t = float(system.tokens.get("bar_thickness", uc * 0.85))
    stem = stem_rect(lsb, lsb + uc, 0.0, cap, prefix="stem.l")
    top = crossbar(system, x0=lsb, x1=lsb + width, cy=cap - bar_t / 2.0, tag_prefix="F.top")
    mid = crossbar(
        system,
        x0=lsb,
        x1=lsb + width * 0.78,
        cy=cap * 0.52,
        tag_prefix="F.mid",
    )
    return stem + top + mid

"""H-group glyph E — stem + three bars."""

from __future__ import annotations

from elements import crossbar, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("E", group="uc.straight")
def glyph_E(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens["E_width"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    bar_t = float(system.tokens.get("bar_thickness", uc * 0.85))
    stem = stem_rect(lsb, lsb + uc, 0.0, cap, prefix="stem.l")
    top = crossbar(system, x0=lsb, x1=lsb + width, cy=cap - bar_t / 2.0, tag_prefix="E.top")
    mid = crossbar(
        system,
        x0=lsb,
        x1=lsb + width * 0.82,
        cy=cap * 0.5,
        tag_prefix="E.mid",
    )
    bot = crossbar(system, x0=lsb, x1=lsb + width, cy=bar_t / 2.0, tag_prefix="E.bot")
    return stem + top + mid + bot

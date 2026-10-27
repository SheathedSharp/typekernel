"""Control glyph H — two stems + bar; corners tagged for future serifs."""

from __future__ import annotations

from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


@glyph("H", group="uc.straight")
def H(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens["H_width"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    bar_t = float(system.tokens.get("bar_thickness", uc * 0.85))
    bar_cy = float(system.tokens.get("bar_height", cap * 0.48))
    x0 = lsb
    x1 = lsb + uc
    x2 = lsb + width - uc
    x3 = lsb + width
    bar_top = bar_cy + bar_t / 2.0
    bar_bot = bar_cy - bar_t / 2.0

    return (
        Writer()
        .start((x0, 0.0))
        .corner("stem.l.foot.o")
        .line((x0, cap))
        .corner("stem.l.top.o")
        .line((x1, cap))
        .corner("stem.l.top.i")
        .line((x1, bar_top))
        .corner("bar.l.top")
        .line((x2, bar_top))
        .corner("bar.r.top")
        .line((x2, cap))
        .corner("stem.r.top.i")
        .line((x3, cap))
        .corner("stem.r.top.o")
        .line((x3, 0.0))
        .corner("stem.r.foot.o")
        .line((x2, 0.0))
        .corner("stem.r.foot.i")
        .line((x2, bar_bot))
        .corner("bar.r.bot")
        .line((x1, bar_bot))
        .corner("bar.l.bot")
        .line((x1, 0.0))
        .corner("stem.l.foot.i")
        .line((x0, 0.0))
        .close()
        .build()
    )

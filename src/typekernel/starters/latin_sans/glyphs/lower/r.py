"""n-group glyph r — stem + short shoulder stub."""

from __future__ import annotations

from elements import WIDTHS, arch_span, stem_rect

from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


@glyph("r", group="lc.straight")
def r(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(WIDTHS["r"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    ov = float(system.overshoot.round) * 0.35
    stem = stem_rect(lsb, lsb + st, 0.0, xh, prefix="stem.l")
    x0 = lsb + st * 0.35
    x1 = lsb + width
    y_top = xh
    y_bot = xh - st * 0.55
    outer = arch_span(x0, y_top, x1, y_top, y_top + ov + 4.0, tension=tension)
    inner = arch_span(x1, y_bot, x0, y_bot, y_bot - 4.0, tension=tension)
    arm = (
        Writer()
        .start((x0, y_bot))
        .corner("arm.l.bot")
        .line((x0, y_top))
        .corner("arm.l.top")
        .fragment(outer)
        .corner("arm.r.top")
        .line((x1, y_bot))
        .corner("arm.r.bot")
        .fragment(inner)
        .close()
        .build()
    )
    return stem + arm

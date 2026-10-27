"""Rest glyph S — stacked open bowls (capital)."""

from __future__ import annotations

# Reuse the lowercase s construction scaled to cap via tokens.
from typekernel.project import glyph
from typekernel.system import System


@glyph("S", group="uc.round")
def glyph_S(system: System):
    # Local import of lowercase builder pattern: two open bowls.
    from elements import arch_span
    from typekernel.draw import Writer

    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens["S_width"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    ov = float(system.overshoot.round)

    def open_bowl(cx, cy, rx, ry, open_right, tag):
        irx = max(rx - st, 1.0)
        iry = max(ry - st * 0.85, 1.0)
        if open_right:
            top = arch_span(cx + rx * 0.35, cy + ry, cx - rx, cy, cy + ry + 6, tension=tension)
            bot = arch_span(cx - rx, cy, cx + rx * 0.35, cy - ry, cy - ry - 6, tension=tension)
            top_i = arch_span(cx - irx, cy, cx + irx * 0.2, cy + iry, cy + iry - st * 0.2, tension=tension)
            bot_i = arch_span(cx + irx * 0.2, cy - iry, cx - irx, cy, cy - iry + st * 0.2, tension=tension)
        else:
            top = arch_span(cx - rx * 0.35, cy + ry, cx + rx, cy, cy + ry + 6, tension=tension)
            bot = arch_span(cx + rx, cy, cx - rx * 0.35, cy - ry, cy - ry - 6, tension=tension)
            top_i = arch_span(cx + irx, cy, cx - irx * 0.2, cy + iry, cy + iry - st * 0.2, tension=tension)
            bot_i = arch_span(cx - irx * 0.2, cy - iry, cx + irx, cy, cy - iry + st * 0.2, tension=tension)
        w = Writer()
        w.start(top.start).corner(f"{tag}.top.o")
        w.fragment(top).corner(f"{tag}.side.o")
        w.fragment(bot).corner(f"{tag}.bot.o")
        w.line(bot_i.start).corner(f"{tag}.bot.i")
        w.fragment(bot_i)
        if abs(bot_i.end.x - top_i.start.x) > 1e-6 or abs(bot_i.end.y - top_i.start.y) > 1e-6:
            w.line(top_i.start)
        w.corner(f"{tag}.side.i")
        w.fragment(top_i).corner(f"{tag}.top.i")
        w.line(top.start)
        return w.close().build()

    cx = lsb + width / 2.0
    rx = width / 2.0 * 0.92
    upper = open_bowl(cx, cap * 0.72, rx, cap * 0.30 + ov * 0.3, True, "S.upper")
    lower = open_bowl(cx, cap * 0.28, rx, cap * 0.30 + ov * 0.3, False, "S.lower")
    return upper + lower

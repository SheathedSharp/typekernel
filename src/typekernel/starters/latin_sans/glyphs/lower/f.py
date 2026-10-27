"""Straight glyph f — ascender stem + bar + top hook."""

from __future__ import annotations

from elements import arch_span, crossbar, stem_rect

from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


@glyph("f", group="lc.straight")
def f(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    asc = float(system.zones.asc)
    width = float(system.tokens["f_width"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    # Stem slightly right of left SB so the top hook can curl left.
    x0 = lsb + width * 0.35
    stem = stem_rect(x0, x0 + st, 0.0, asc - st * 0.8, prefix="stem")
    bar = crossbar(
        system,
        x0=lsb + st * 0.15,
        x1=lsb + width - st * 0.1,
        cy=xh,
        tag_prefix="f.bar",
    )
    # Top hook curling left from stem top.
    y_join = asc - st * 0.8
    tip_x = lsb + st * 0.2
    outer = arch_span(x0 + st, y_join, tip_x, asc - st * 0.15, asc + 4.0, tension=tension)
    inner = arch_span(
        tip_x + st * 0.65,
        asc - st * 0.85,
        x0,
        y_join,
        asc - st * 0.55,
        tension=tension,
    )
    hook = (
        Writer()
        .start((x0, y_join))
        .corner("f.hook.stem.l")
        .line((x0 + st, y_join))
        .corner("f.hook.stem.r")
        .fragment(outer)
        .corner("f.hook.tip.o")
        .line((tip_x + st * 0.65, asc - st * 0.85))
        .corner("f.hook.tip.i")
        .fragment(inner)
        .close()
        .build()
    )
    return stem + bar + hook

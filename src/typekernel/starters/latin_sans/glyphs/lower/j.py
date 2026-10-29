"""Straight glyph j — descender stem with hook + tittle."""

from __future__ import annotations

from elements import WIDTHS, arch_span, stem_rect

from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


@glyph("j", group="lc.straight")
def j(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    desc = float(system.zones.desc)
    width = float(WIDTHS["j"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    x0 = lsb + (width - st) / 2.0
    # Main stem from descender hook join up to x-height.
    hook_y = desc + st * 1.1
    stem = stem_rect(x0, x0 + st, hook_y, xh, prefix="stem")
    # Hook trough at bottom curling left.
    x_l = x0 + st - width * 0.85
    outer = arch_span(x0 + st, hook_y, x_l, desc + st * 0.2, desc - 4.0, tension=tension)
    inner = arch_span(
        x_l + st * 0.7,
        desc + st * 0.85,
        x0,
        hook_y,
        desc + st * 1.35,
        tension=tension,
    )
    hook = (
        Writer()
        .start((x0, hook_y))
        .corner("hook.stem.l")
        .line((x0 + st, hook_y))
        .corner("hook.stem.r")
        .fragment(outer)
        .corner("hook.tip.o")
        .line((x_l + st * 0.7, desc + st * 0.85))
        .corner("hook.tip.i")
        .fragment(inner)
        .close()
        .build()
    )
    # Tittle
    dot_r = st * 0.55
    cy = xh + float(system.overshoot.round) + dot_r * 1.15
    cx = x0 + st / 2.0
    tittle = stem_rect(cx - dot_r, cx + dot_r, cy - dot_r, cy + dot_r, prefix="tittle")
    return stem + hook + tittle

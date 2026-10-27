"""Rest glyph J — stem with bottom hook."""

from __future__ import annotations

from elements import arch_span, stem_rect

from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


@glyph("J", group="uc.straight")
def glyph_J(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens["J_width"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    x0 = lsb + width - st
    hook_y = st * 1.2
    stem = stem_rect(x0, x0 + st, hook_y, cap, prefix="stem")
    tip_x = lsb + st * 0.3
    outer = arch_span(x0 + st, hook_y, tip_x, st * 0.25, -6.0, tension=tension)
    inner = arch_span(
        tip_x + st * 0.75, st * 0.95, x0, hook_y, st * 1.4, tension=tension
    )
    hook = (
        Writer()
        .start((x0, hook_y))
        .corner("J.hook.stem.l")
        .line((x0 + st, hook_y))
        .corner("J.hook.stem.r")
        .fragment(outer)
        .corner("J.hook.tip.o")
        .line((tip_x + st * 0.75, st * 0.95))
        .corner("J.hook.tip.i")
        .fragment(inner)
        .close()
        .build()
    )
    return stem + hook

"""Mixed glyph f — anatomy stem + crossbar + arch hook (P3-7)."""

from __future__ import annotations

from elements import WIDTHS, arch_span

from typekernel.anatomy import crossbar, stem
from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


@glyph("f", group="lc.mixed")
def f(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    asc = float(system.zones.asc)
    width = float(WIDTHS["f"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    x0 = lsb + width * 0.35
    y_join = asc - st * 0.8
    body = stem(x0, x0 + st, 0.0, y_join, name="stem", top="none")
    bar = crossbar(
        lsb + st * 0.15,
        lsb + width - st * 0.1,
        xh,
        thick=thin,
        name="bar",
        ends="none",
    )
    # Signature-stable hook (same arch_span recipe as j); anatomy.hook flips
    # winding across Light/Bold and breaks compat.signature.
    tip_x = lsb + st * 0.2
    outer = arch_span(
        x0 + st, y_join, tip_x, asc - st * 0.15, asc + 4.0, tension=tension
    )
    inner = arch_span(
        tip_x + st * 0.65,
        asc - st * 0.85,
        x0,
        y_join,
        asc - st * 0.55,
        tension=tension,
    )
    curl = (
        Writer()
        .start((x0, y_join))
        .corner("hook.entry")
        .line((x0 + st, y_join))
        .corner("hook.stem")
        .fragment(outer)
        .corner("hook.tip.o")
        .line((tip_x + st * 0.65, asc - st * 0.85))
        .corner("hook.tip.i")
        .fragment(inner)
        .close()
        .build()
    )
    return body + bar + curl

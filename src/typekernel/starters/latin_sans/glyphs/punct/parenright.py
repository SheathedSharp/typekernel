"""parenright — mirror of parenleft (one island; stock self-crossed)."""

from __future__ import annotations

from elements import arch_span

from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


@glyph("parenright", group="punct")
def parenright(system: System):
    st = float(system.stem["lc"])
    asc = float(system.zones.asc)
    desc = float(system.zones.desc)
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.5
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    # Same cup as parenleft, then mirror across the stem center so opening faces left.
    x_outer = lsb + st * 1.6
    x_inner = lsb + st * 0.55
    outer = arch_span(x_outer, asc, x_outer, desc + st, lsb - 4, tension=tension)
    inner = arch_span(
        x_inner, desc + st * 1.2, x_inner, asc - st * 0.2, lsb + st * 0.9, tension=tension
    )
    left_cup = (
        Writer()
        .start(outer.start)
        .corner("arch.t.o")
        .fragment(outer)
        .corner("arch.b.o")
        .line(inner.start)
        .corner("arch.b.i")
        .fragment(inner)
        .corner("arch.t.i")
        .line(outer.start)
        .close()
        .build()
    )
    axis = (x_outer + x_inner) / 2.0
    return left_cup.mirrored_x(axis)

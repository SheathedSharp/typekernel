"""parenright — arch_span cup (P3-7; signature-stable)."""

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
    width = st * 2.2
    x_outer = lsb + st * 0.4
    x_inner = lsb + st * 1.45
    outer = arch_span(x_outer, asc, x_outer, desc + st, lsb + width + 4, tension=tension)
    inner = arch_span(
        x_inner, desc + st * 1.2, x_inner, asc - st * 0.2, lsb + width - st * 0.5, tension=tension
    )
    return (
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

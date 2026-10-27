"""parenright — mirror of parenleft."""

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
    inner = arch_span(x_inner, desc + st * 1.2, x_inner, asc - st * 0.2, lsb + width - st * 0.5, tension=tension)
    w = Writer()
    w.start(outer.start).corner("paren.top.o")
    w.fragment(outer).corner("paren.bot.o")
    w.line(inner.start).corner("paren.bot.i")
    w.fragment(inner).corner("paren.top.i")
    w.line(outer.start)
    return w.close().build()

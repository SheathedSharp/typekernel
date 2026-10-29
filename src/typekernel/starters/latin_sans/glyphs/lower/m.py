"""n-group glyph m — three stems + two anatomy arches (P3-7)."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import arch, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("m", group="lc.straight")
def m(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    width = float(WIDTHS["m"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    ov = float(system.overshoot.round)
    gap = (width - 3.0 * st) / 2.0
    x0 = lsb
    x1 = lsb + st + gap
    x2 = lsb + width - st
    left = stem(x0, x0 + st, 0.0, xh, name="stem.l")
    mid = stem(x1, x1 + st, 0.0, xh, name="stem.1")
    right = stem(x2, x2 + st, 0.0, xh, name="stem.r")
    arch1 = arch(
        x0 + st,
        x1,
        height=xh,
        thick=st,
        thin=thin,
        join_depth=st * 0.45,
        tension=tension,
        overshoot=ov * 0.35,
        name="arch.0",
    )
    arch2 = arch(
        x1 + st,
        x2,
        height=xh,
        thick=st,
        thin=thin,
        join_depth=st * 0.45,
        tension=tension,
        overshoot=ov * 0.35,
        name="arch.1",
    )
    return left + mid + right + arch1 + arch2

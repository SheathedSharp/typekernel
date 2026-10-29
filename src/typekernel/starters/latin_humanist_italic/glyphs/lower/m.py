"""n-group glyph m — two n-arches with mid gap (G-class clean)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("m", group="lc.straight")
def m(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("m_width", 640.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    rise = float(system.tokens.get("arch_rise", 0.12)) * xh
    x0 = lsb + st * 0.5
    x2 = lsb + width - st * 0.5
    x1 = (x0 + x2) / 2.0
    # Keep arches from overlapping at mid — fused mid stems mid-lerp SI.
    sep = 60.0

    def arch(xa: float, xb: float):
        mid = (xa + xb) / 2.0
        return stroke(
            system,
            [
                (xa, 0.0),
                (xa, xh - rise),
                (xa + (xb - xa) * 0.15, xh),
                (mid, xh + rise * 0.15),
                (xb - (xb - xa) * 0.15, xh),
                (xb, xh - rise),
                (xb, 0.0),
            ],
            thickness=st,
        )

    return arch(x0, x1 - sep) + arch(x1 + sep, x2)

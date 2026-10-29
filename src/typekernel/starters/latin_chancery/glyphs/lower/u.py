"""u — fused stem/baseline/stem rail (interpolation-safe; shallow cup self-intersection)."""

from __future__ import annotations

from elements import fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("u", group="lc.straight")
def u(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("n_width", 420.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    x0 = lsb + st * 0.5
    x1 = lsb + width - st * 0.5
    return fuse(
        stroke(system, [(x0, xh), (x0, 0.0), (x1, 0.0), (x1, xh)], thickness=st)
    )

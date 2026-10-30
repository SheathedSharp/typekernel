"""k — stem + two horizontal arms (interpolation-safe; acute diags self-intersection under slant)."""

from __future__ import annotations

from elements import WIDTHS, fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("k", group="lc.diag")
def k(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    asc = float(system.zones.asc)
    width = float(WIDTHS.get("k", 420.0))
    lsb = float(system.tokens["lsb_lc"])
    x0 = lsb + st * 0.5
    x1 = lsb + width - st * 0.25
    return fuse(
        stroke(system, [(x0, 0.0), (x0, asc)], thickness=st)
        + stroke(system, [(x0, xh * 0.75), (x1, xh * 0.75)], thickness=st)
        + stroke(system, [(x0, xh * 0.25), (x1, xh * 0.25)], thickness=st)
    )

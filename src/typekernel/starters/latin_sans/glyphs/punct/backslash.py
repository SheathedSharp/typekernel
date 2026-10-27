"""backslash — reverse solidus."""

from __future__ import annotations

import math

from elements import diagonal_stroke

from typekernel.plugins.passes.diagonal_comp import compensated_weight
from typekernel.project import glyph
from typekernel.system import System


@glyph("backslash", group="punct")
def backslash(system: System):
    st = float(system.stem["lc"])
    asc = float(system.zones.asc)
    desc = float(system.zones.desc)
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.4
    width = float(system.tokens.get("slash_width", 320))
    ang = math.degrees(math.atan2(width, asc - desc))
    wt = compensated_weight(st, ang)
    return diagonal_stroke(
        (lsb + st * 0.2, asc),
        (lsb + width - st * 0.2, desc),
        weight=wt,
        tag_prefix="backslash",
    )

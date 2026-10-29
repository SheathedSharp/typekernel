"""slash — solidus diagonal."""

from __future__ import annotations

import math

from elements import WIDTHS, diagonal_stroke

from typekernel.plugins.passes.diagonal_comp import compensated_weight
from typekernel.project import glyph
from typekernel.system import System


@glyph("slash", group="punct")
def slash(system: System):
    st = float(system.stem["lc"])
    asc = float(system.zones.asc)
    desc = float(system.zones.desc)
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.4
    width = float(WIDTHS.get("slash", 320))
    ang = math.degrees(math.atan2(width, asc - desc))
    wt = compensated_weight(st, ang)
    return diagonal_stroke(
        (lsb + width - st * 0.2, asc),
        (lsb + st * 0.2, desc),
        weight=wt,
        tag_prefix="slash",
    )

"""Figure 7 — top bar + diagonal."""
from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("seven", group="figs")
def seven(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 420.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    h = float(system.zones.cap) * 0.72
    top = stroke(
        system, [(lsb + st * 0.2, h), (lsb + width - st * 0.2, h)],
        thickness=float(system.stem["lc_h"]),
    )
    diag = stroke(
        system, [(lsb + width - st * 0.3, h), (lsb + width * 0.35, 0.0)], thickness=st,
    )
    return top + diag

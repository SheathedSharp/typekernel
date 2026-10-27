"""Figure 4 — open triangle + stem (skeleton+pen)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("four", group="figs")
def four(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 460.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    h = float(system.zones.cap) * 0.72
    x_stem = lsb + width * 0.68
    stem = stroke(system, [(x_stem, 0.0), (x_stem, h)], thickness=st)
    arm = stroke(
        system,
        [(lsb + width * 0.12, h * 0.42), (x_stem + st * 0.2, h * 0.42), (lsb + width * 0.35, h)],
        thickness=st,
    )
    return stem + arm

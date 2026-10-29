"""Figure 4 — spine + gapped crossbar (P5-2 G-class)."""

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
    x_stem = lsb + width * 0.72
    y_bar = h * 0.38
    # Continuous open spine (diag into stem); bar stops short of stem join.
    spine = stroke(
        system,
        [(lsb + width * 0.12, h), (x_stem, y_bar), (x_stem, 0.0)],
        thickness=st,
    )
    bar = stroke(
        system,
        [(lsb + width * 0.08, y_bar), (x_stem - st * 1.2, y_bar)],
        thickness=st,
    )
    return spine + bar

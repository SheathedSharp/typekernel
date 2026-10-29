"""Figure 4 — open triangle: diagonal + crossbar + stem (P5-2; closes A-14)."""

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
    stem = stroke(system, [(x_stem, 0.0), (x_stem, h)], thickness=st)
    cross = stroke(
        system,
        [(lsb + width * 0.08, y_bar), (x_stem + st * 0.35, y_bar)],
        thickness=st,
    )
    diag = stroke(
        system,
        [(lsb + width * 0.12, h), (x_stem, y_bar)],
        thickness=st,
    )
    return stem + cross + diag

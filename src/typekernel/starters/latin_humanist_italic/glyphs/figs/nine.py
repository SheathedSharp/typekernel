"""Figure 9 — bowl with lower stem (skeleton+pen)."""

from __future__ import annotations

from elements import oval_points, open_arc_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("nine", group="figs")
def nine(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 460.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    h = float(system.zones.cap) * 0.72
    cx = lsb + width / 2.0
    bowl = stroke(
        system,
        oval_points(cx, h * 0.68, width * 0.38, h * 0.28),
        closed=True,
        thickness=st,
    )
    spine = stroke(
        system,
        open_arc_points(cx, h * 0.40, width * 0.40, h * 0.42, start_deg=20.0, end_deg=-90.0, n=14),
        thickness=st,
    )
    return bowl + spine

"""Figure 5 — top bar + spine + lower bowl (skeleton+pen)."""

from __future__ import annotations

from elements import open_arc_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("five", group="figs")
def five(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 460.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    h = float(system.zones.cap) * 0.72
    top = stroke(system, [(lsb + width * 0.15, h), (lsb + width * 0.85, h)], thickness=st)
    spine = stroke(system, [(lsb + width * 0.22, h), (lsb + width * 0.22, h * 0.48)], thickness=st)
    bowl = stroke(
        system,
        open_arc_points(
            lsb + width * 0.48, h * 0.30, width * 0.38, h * 0.30, start_deg=160.0, end_deg=-40.0, n=16
        ),
        thickness=st,
    )
    return top + spine + bowl

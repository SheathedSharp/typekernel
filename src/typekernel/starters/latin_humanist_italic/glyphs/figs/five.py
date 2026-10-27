"""Figure 5 — top bar + continuous spine into lower open_bowl."""

from __future__ import annotations

from elements import open_bowl, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("five", group="figs")
def five(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 460.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    h = float(system.zones.cap) * 0.72
    # Continuous open skeleton: top bar into spine down to bowl join.
    x_spine = lsb + width * 0.22
    top_spine = stroke(
        system,
        [
            (lsb + width * 0.82, h),
            (x_spine, h),
            (x_spine, h * 0.48),
        ],
        thickness=st,
    )
    # Lower bowl open on the left so it nests against the spine foot.
    bowl = open_bowl(
        system,
        cx=lsb + width * 0.52,
        cy=h * 0.30,
        rx=width * 0.38,
        ry=h * 0.30,
        thickness=st,
        open_side="left",
        aperture_deg=85.0,
    )
    return top_spine + bowl

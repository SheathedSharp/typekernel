"""Figure 6 — bowl with upper-left hook stem."""

from __future__ import annotations

from elements import bowl, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("six", group="figs")
def six(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 500))
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    h = float(system.zones.cap) * 0.72
    ov = float(system.overshoot.round) * 0.4
    bowl_ = bowl(
        system,
        cx=lsb + width * 0.52,
        cy=h * 0.35,
        rx=width * 0.42,
        ry=h * 0.32 + ov,
        thickness=st,
    )
    stem = stem_rect(lsb + st * 0.3, lsb + st * 1.3, h * 0.35, h, prefix="six.stem")
    return bowl_ + stem

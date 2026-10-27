"""Figure 9 — upper bowl + descending stem."""

from __future__ import annotations

from elements import bowl, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("nine", group="figs")
def nine(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 500))
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    h = float(system.zones.cap) * 0.72
    ov = float(system.overshoot.round) * 0.4
    bowl_ = bowl(
        system,
        cx=lsb + width * 0.48,
        cy=h * 0.62,
        rx=width * 0.42,
        ry=h * 0.30 + ov,
        thickness=st,
    )
    stem = stem_rect(lsb + width - st * 1.3, lsb + width - st * 0.3, 0.0, h * 0.62, prefix="nine.stem")
    return bowl_ + stem

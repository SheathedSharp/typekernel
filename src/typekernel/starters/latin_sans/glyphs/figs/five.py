"""Figure 5 — top bar + stem stub + lower bowl."""

from __future__ import annotations

from elements import WIDTHS, bowl, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("five", group="figs")
def five(system: System):
    st = float(system.stem["lc"])
    width = float(WIDTHS.get("fig", 500))
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    h = float(system.zones.cap) * 0.72
    ov = float(system.overshoot.round) * 0.4
    top = stem_rect(lsb, lsb + width * 0.85, h - st, h, prefix="five.top")
    stub = stem_rect(lsb, lsb + st, h * 0.42, h - st * 0.5, prefix="five.stub")
    bowl_ = bowl(
        system,
        cx=lsb + width * 0.55,
        cy=h * 0.32,
        rx=width * 0.42,
        ry=h * 0.30 + ov,
        thickness=st,
    )
    return top + stub + bowl_

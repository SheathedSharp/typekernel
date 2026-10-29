"""Straight glyph T — anatomy centered stem + top bar ."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import crossbar, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("T", group="uc.straight")
def glyph_T(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["T"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    bar_t = float(system.tokens.get("bar_thickness", uc * 0.85))
    x0 = lsb + (width - uc) / 2.0
    body = stem(x0, x0 + uc, 0.0, cap, name="stem")
    bar = crossbar(
        lsb,
        lsb + width,
        cap - bar_t / 2.0,
        thick=bar_t,
        name="bar",
        ends="none",
    )
    return zone_anchors(body + bar, system, top='cap')

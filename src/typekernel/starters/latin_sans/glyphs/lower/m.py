"""n-group glyph m — three stems + two overlapping shoulders."""

from __future__ import annotations

from elements import WIDTHS, shoulder_trough, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("m", group="lc.straight")
def m(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(WIDTHS["m"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    inset = st * 0.35
    # Three stems evenly spanning width.
    gap = (width - 3.0 * st) / 2.0
    x0 = lsb
    x1 = lsb + st + gap
    x2 = lsb + width - st
    left = stem_rect(x0, x0 + st, 0.0, xh, prefix="stem.l")
    mid = stem_rect(x1, x1 + st, 0.0, xh, prefix="stem.m")
    right = stem_rect(x2, x2 + st, 0.0, xh, prefix="stem.r")
    y_bot = xh - st + float(system.overshoot.round) * 0.35
    arch1 = shoulder_trough(
        system,
        x_left=x0 + inset,
        x_right=x1 + st - inset,
        y_top=xh,
        y_bot=y_bot,
        tag_prefix="arch.1",
    )
    arch2 = shoulder_trough(
        system,
        x_left=x1 + inset,
        x_right=x2 + st - inset,
        y_top=xh,
        y_bot=y_bot,
        tag_prefix="arch.2",
    )
    return left + mid + right + arch1 + arch2

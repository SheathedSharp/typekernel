"""Italic control sheet keeps topology."""

from __future__ import annotations

import math

import pytest

from typekernel.axes.interpolatable import check_interpolatable
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import Controls, DesignContext
from typekernel.parts.italic import italic_controls


def _stem_slant_degrees(glyph, y_lo: float, y_hi: float) -> float:
    def left_edge(y: float) -> float:
        intervals = ink_intervals_at_y(list(glyph.solids), y)
        return intervals[0][0] if intervals else 0.0

    x_lo, x_hi = left_edge(y_lo), left_edge(y_hi)
    return math.degrees(math.atan2(x_hi - x_lo, y_hi - y_lo))


@pytest.mark.xfail(strict=True, reason="M4: italic_controls is not a slanted master yet")
def test_italic_master_has_readable_slant() -> None:
    ctx = DesignContext.humanist_sans()
    glyph = italic_controls(Controls.from_context(ctx)).build_all("l")["l"]
    slant = _stem_slant_degrees(glyph, ctx.x_height * 0.15, ctx.x_height * 0.85)
    assert slant >= 6.0


def test_italic_and_regular_interpolate() -> None:
    ctx = DesignContext.code_clear()
    reg = Controls.from_context(ctx).build_all("a")
    ital = italic_controls(Controls.from_context(ctx)).build_all("a")
    assert check_interpolatable([reg["a"].solids[0], ital["a"].solids[0]]) == []

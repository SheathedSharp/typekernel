"""Italic control sheet keeps topology."""

from __future__ import annotations

import math

import pytest

from typekernel.axes.interpolatable import check_interpolatable
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import DesignContext, FormSources
from typekernel.parts.italic import italic_controls, italic_design


def _stem_slant_degrees(glyph, y_lo: float, y_hi: float) -> float:
    def left_edge(y: float) -> float:
        intervals = ink_intervals_at_y(list(glyph.solids), y)
        return intervals[0][0] if intervals else 0.0

    x_lo, x_hi = left_edge(y_lo), left_edge(y_hi)
    return math.degrees(math.atan2(x_hi - x_lo, y_hi - y_lo))


def test_italic_master_has_readable_slant() -> None:
    ctx = DesignContext.humanist_sans()
    glyph = italic_design(FormSources.from_context(ctx)).derive("l")["l"]
    slant = _stem_slant_degrees(glyph, ctx.x_height * 0.15, ctx.x_height * 0.85)
    assert slant >= 6.0


def test_italic_construct_slant_matches_target_within_half_degree() -> None:
    """M4 acceptance: measured stem slant vs ``italic_slant_deg``."""
    for preset in ("code_clear", "humanist_sans", "geometric_sans"):
        ctx = getattr(DesignContext, preset)()
        ital = italic_design(FormSources.from_context(ctx))
        target = ital.context.italic_slant_deg
        y_lo, y_hi = ctx.x_height * 0.15, ctx.x_height * 0.85
        for ch in "iln":
            measured = _stem_slant_degrees(ital.derive_one(ch), y_lo, y_hi)
            assert measured == pytest.approx(target, abs=0.5)


def test_italic_design_matches_italic_controls_default() -> None:
    ctx = DesignContext.code_clear()
    reg = FormSources.from_context(ctx)
    with pytest.warns(DeprecationWarning, match="italic_controls"):
        a = italic_controls(reg).derive_one("l")
    b = italic_design(reg).derive_one("l")
    assert a.solids[0].contours[0].segments[0].points[0].x == pytest.approx(
        b.solids[0].contours[0].segments[0].points[0].x
    )


def test_italic_and_regular_interpolate_on_vf_oblique_compat() -> None:
    ctx = DesignContext.code_clear()
    from typekernel.parts.italic import vf_upright_controls

    base = vf_upright_controls(FormSources.from_context(ctx))
    reg = base.derive("o")
    ital = italic_design(base).derive("o")
    assert check_interpolatable([reg["o"].solids[0], ital["o"].solids[0]]) == []

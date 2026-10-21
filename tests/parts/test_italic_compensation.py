"""TK-402: horizontal stroke compensation before construct slant."""

from __future__ import annotations

from typekernel.optics.stem import measure_oriented_stem
from typekernel.parts import DesignContext, FormSources
from typekernel.parts.control import o_metrics
from typekernel.parts.italic import horizontal_slant_compensation, italic_design
from typekernel.qa.thickness import measurement_outline


def _horizontal_width_at_y(glyph, y: float) -> float:
    outline = measurement_outline(glyph)
    intervals = measure_oriented_stem(outline, (500.0, y), 0.0)
    assert intervals is not None
    return intervals


def test_horizontal_slant_compensation_is_secant() -> None:
    ctx = DesignContext.code_clear().tuned(italic_slant_deg=10.0)
    assert horizontal_slant_compensation(ctx) > 1.01
    assert horizontal_slant_compensation(DesignContext.code_clear()) == 1.0


def test_italic_o_top_stroke_near_upright_after_slant() -> None:
    ctx = DesignContext.geometric_sans()
    reg = FormSources.from_context(ctx).derive_one("o")
    ital = italic_design(FormSources.from_context(ctx)).derive_one("o")
    m = o_metrics(ctx)
    outline_reg = measurement_outline(reg)
    outline_ital = measurement_outline(ital)
    cx = m.rx
    top_y = m.x_height + m.overshoot * 0.5
    w_reg = measure_oriented_stem(outline_reg, (cx, top_y - m.thickness_h * 0.5), 0.0)
    w_ital = measure_oriented_stem(
        outline_ital, (cx, top_y - m.thickness_h * 0.5), 0.0
    )
    assert w_reg is not None and w_ital is not None
    assert w_ital >= w_reg * 0.94


def test_italic_e_crossbar_not_thinner_than_upright_after_slant() -> None:
    ctx = DesignContext.code_clear()
    reg = FormSources.from_context(ctx).derive_one("e")
    ital = italic_design(FormSources.from_context(ctx)).derive_one("e")
    y = ctx.x_height * 0.52
    w_reg = _horizontal_width_at_y(reg, y)
    w_ital = _horizontal_width_at_y(ital, y)
    assert w_ital >= w_reg * 0.94
    assert w_ital <= w_reg * 1.08

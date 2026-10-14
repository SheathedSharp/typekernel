"""TK-402: horizontal stroke compensation before construct slant."""

from __future__ import annotations

from typekernel.optics.stem import measure_oriented_stem
from typekernel.parts import Controls, DesignContext
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


def test_italic_e_crossbar_not_thinner_than_upright_after_slant() -> None:
    ctx = DesignContext.code_clear()
    reg = Controls.from_context(ctx).build("e")
    ital = italic_design(Controls.from_context(ctx)).build("e")
    y = ctx.x_height * 0.52
    w_reg = _horizontal_width_at_y(reg, y)
    w_ital = _horizontal_width_at_y(ital, y)
    assert w_ital >= w_reg * 0.94
    assert w_ital <= w_reg * 1.08

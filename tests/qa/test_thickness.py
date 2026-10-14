"""Local thickness metric calibration (TK-102 fixtures)."""

from __future__ import annotations

import pytest

from typekernel.optics.stem import measure_oriented_stem
from typekernel.parts import Controls, DesignContext
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.control import o_metrics
from typekernel.parts.primitives import vertical_stem
from typekernel.qa.lint import lint_controls
from typekernel.qa.thickness import (
    HOOK_MIN_THIN_RATIO,
    THICKNESS_OUTLIER_FACTOR,
    max_local_thickness,
    measurement_outline,
    min_hook_thickness,
    thickness_ratio_to_stem,
)

_O_RING_MAX_RATIO = 1.10
_STEM_TOLERANCE = 0.02


def _stem_rect_glyph(ctx: DesignContext) -> ComposedGlyph:
    outline = vertical_stem(ctx, 0.0, 0.0, ctx.x_height, width=ctx.stem)
    return ComposedGlyph((outline,), (), ctx.stem * 1.2, ctx)


@pytest.mark.parametrize(
    ("preset", "max_ratio"),
    [
        ("humanist_sans", 1.0),
        ("geometric_sans", 1.07),
        ("code_clear", 1.08),
    ],
)
def test_o_ring_thickness_near_stem(preset: str, max_ratio: float) -> None:
    factory = getattr(DesignContext, preset)
    ctx = factory()
    glyph = Controls.from_context(ctx).build_all("o")["o"]
    ratio = thickness_ratio_to_stem(glyph, ctx.stem)
    assert ratio <= _O_RING_MAX_RATIO
    assert ratio >= max_ratio * 0.98


def test_o_contrast_top_to_side_thickness_ratio() -> None:
    """TK-301: horizontal ring stroke ÷ vertical side stroke ≈ contrast."""
    ctx = DesignContext.geometric_sans().tuned(contrast=0.5, stem=100.0)
    glyph = Controls.from_context(ctx).build_all("o")["o"]
    m = o_metrics(ctx)
    outline = measurement_outline(glyph)
    cx = m.rx
    top_y = m.x_height + m.overshoot * 0.5
    side_x = m.rx * 2.0 - m.thickness_v * 0.5
    cy = m.x_height / 2.0
    top_w = measure_oriented_stem(outline, (cx, top_y - m.thickness_h * 0.5), 0.0)
    side_w = measure_oriented_stem(outline, (side_x, cy), 90.0)
    assert top_w is not None and side_w is not None
    assert abs(top_w / side_w - ctx.contrast) <= 0.05


def test_vertical_stem_measures_stem_width() -> None:
    ctx = DesignContext.code_clear()
    glyph = _stem_rect_glyph(ctx)
    measured = max_local_thickness(glyph)
    assert abs(measured - ctx.stem) <= ctx.stem * _STEM_TOLERANCE


def test_m_thickness_within_control_band() -> None:
    controls = Controls.from_context(DesignContext.humanist_sans())
    report = lint_controls(controls, "mn", thickness=True)
    rules = {(i.glyph, i.rule) for i in report.issues}
    assert ("m", "R9_thickness_outlier") not in rules
    assert ("n", "R9_thickness_outlier") not in rules


def test_thickness_outlier_factor_frozen() -> None:
    assert THICKNESS_OUTLIER_FACTOR == 1.15


@pytest.mark.parametrize("char", ("f", "t", "g", "J"))
def test_hook_root_thickness(char: str) -> None:
    ctx = DesignContext.humanist_sans()
    glyphs = Controls.from_context(ctx).build_all(char)
    floor = ctx.thin * HOOK_MIN_THIN_RATIO
    assert min_hook_thickness(glyphs[char], char, ctx) >= floor


def test_j_hook_root_thickness_on_body() -> None:
    ctx = DesignContext.humanist_sans()
    j = Controls.from_context(ctx).build_all("j")["j"]
    body = ComposedGlyph((j.solids[0],), (), j.advance, ctx)
    floor = ctx.thin * HOOK_MIN_THIN_RATIO
    assert min_hook_thickness(body, "j", ctx) >= floor

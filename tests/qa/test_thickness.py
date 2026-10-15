"""Local thickness metric calibration (TK-102 fixtures)."""

from __future__ import annotations

import pytest

from typekernel.parts import Controls, DesignContext
from typekernel.parts.caps import HMetrics
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.control import OMetrics, o_metrics
from typekernel.parts.primitives import vertical_stem
from typekernel.qa.lint import lint_controls
from typekernel.qa.thickness import (
    HOOK_MIN_THIN_RATIO,
    HOOK_MIN_THIN_RATIO_DISPLAY,
    HOOK_MIN_THIN_RATIO_SOFT,
    M_CROTCH_SHELF_MIN_OVER_STEM,
    THICKNESS_OUTLIER_FACTOR,
    figure_bar_over_stem_ink_ratio,
    figure_nine_bar_over_stem_ink_ratio,
    figure_stacked_ring_ink_ratio,
    hook_min_thin_floor,
    m_crotch_shelf_thickness_over_stem,
    max_local_thickness,
    min_hook_thickness,
    ometrics_ink_horizontal_over_vertical_ratio,
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


def _o_horizontal_over_vertical_thickness(ctx: DesignContext) -> float:
    glyph = Controls.from_context(ctx).build_all("o")["o"]
    return ometrics_ink_horizontal_over_vertical_ratio(glyph)


def test_o_contrast_top_to_side_thickness_ratio() -> None:
    """TK-301: horizontal ring stroke ÷ vertical side stroke ≈ contrast."""
    ctx = DesignContext.geometric_sans().tuned(contrast=0.5, stem=100.0)
    ratio = _o_horizontal_over_vertical_thickness(ctx)
    assert abs(ratio - ctx.contrast) <= 0.05


@pytest.mark.parametrize("preset", ("display", "open_print"))
def test_o_metrics_thickness_h_reflects_contrast(preset: str) -> None:
    """Wide-aperture presets: side ink probe misses mid-height; metrics still track contrast."""
    ctx = getattr(DesignContext, preset)()
    m = o_metrics(ctx)
    assert abs(m.thickness_h / m.thickness_v - ctx.contrast) <= 1e-6


@pytest.mark.parametrize("char", ("0", "G", "Q", "S"))
def test_cap_round_glyph_ometrics_tracks_contrast(char: str) -> None:
    """TK-301: built glyph ``OMetrics`` horizontal ÷ vertical stroke ≈ ``contrast``."""
    ctx = DesignContext.geometric_sans().tuned(contrast=0.73, stem=92.0)
    glyph = Controls.from_context(ctx).build(char)
    design = glyph.design
    assert isinstance(design, OMetrics)
    assert abs(design.thickness_h / design.thickness_v - ctx.contrast) <= 1e-5


@pytest.mark.parametrize("char", ("3", "5", "8", "9"))
def test_lining_figure_hmetrics_bar_tracks_contrast(char: str) -> None:
    """TK-301: figure ``H`` record bar thickness follows ``stem * contrast * 0.92``."""
    ctx = DesignContext.geometric_sans().tuned(contrast=0.73, stem=92.0)
    glyph = Controls.from_context(ctx).build(char)
    design = glyph.design
    assert isinstance(design, HMetrics)
    assert abs(design.bar / design.stem - ctx.contrast * 0.92) <= 1e-5


def test_lowercase_s_carries_o_contrast_in_design() -> None:
    ctx = DesignContext.humanist_sans().tuned(contrast=0.58, stem=80.0)
    glyph = Controls.from_context(ctx).build("s")
    design = glyph.design
    assert isinstance(design, OMetrics)
    assert abs(design.thickness_h / design.thickness_v - ctx.contrast) <= 1e-5


_CONTRAST_INK_TOLERANCE = 0.05
_FIGURE_BAR_STEM_TOLERANCE = 0.06
_FIGURE_RING_INK_TOLERANCE = 0.06


@pytest.mark.parametrize(
    ("char", "side_y_fraction", "side_x_fraction"),
    (
        ("Q", 0.5, None),
        ("G", 0.35, None),
        ("S", 0.732, 0.09),
    ),
)
def test_ometrics_ink_contrast_ratio(
    char: str, side_y_fraction: float, side_x_fraction: float | None
) -> None:
    """TK-301: ring ink thickness ratio ≈ ``contrast`` (``measure_oriented_stem``)."""
    ctx = DesignContext.geometric_sans().tuned(contrast=0.73, stem=92.0)
    glyph = Controls.from_context(ctx).build(char)
    ratio = ometrics_ink_horizontal_over_vertical_ratio(
        glyph,
        side_y_fraction=side_y_fraction,
        side_x_fraction=side_x_fraction,
    )
    assert abs(ratio - ctx.contrast) <= _CONTRAST_INK_TOLERANCE


@pytest.mark.parametrize(
    ("char", "waist", "expected_scale"),
    (
        ("5", None, 0.92),
        ("8", 0.54, 1.0),
        ("9", None, 0.92),
    ),
)
def test_figure_ink_contrast_ratio(
    char: str, waist: float | None, expected_scale: float
) -> None:
    """TK-301: figure bar/ring ink probes track contrast (not only ``OMetrics``)."""
    ctx = DesignContext.geometric_sans().tuned(contrast=0.73, stem=92.0)
    glyph = Controls.from_context(ctx).build(char)
    expected = ctx.contrast * expected_scale
    if char == "5":
        ratio = figure_bar_over_stem_ink_ratio(glyph)
    elif char == "8":
        assert waist is not None
        ratio = figure_stacked_ring_ink_ratio(glyph, waist=waist)
    else:
        ratio = figure_nine_bar_over_stem_ink_ratio(glyph)
    if expected_scale < 1.0:
        tol = _FIGURE_BAR_STEM_TOLERANCE
    elif char == "8":
        tol = _FIGURE_RING_INK_TOLERANCE
    else:
        tol = _CONTRAST_INK_TOLERANCE
    assert abs(ratio - expected) <= tol


@pytest.mark.parametrize("char", ("3", "5", "8", "9", "G", "Q", "S"))
def test_contrast_moves_figures_and_round_caps(char: str) -> None:
    """TK-301: digits and cap round forms must respond to contrast (not only via ``o`` probe)."""
    from tests.parts.test_knob_coverage import _shape_changed

    base = DesignContext.display()
    controls = Controls.from_context(base)
    tuned = Controls.from_context(base.tuned(contrast=0.55))
    before = {char: controls.build(char)}
    after = {char: tuned.build(char)}
    assert char in _shape_changed(before, after)


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


@pytest.mark.parametrize("preset", ("humanist_sans", "code_clear", "geometric_sans"))
def test_m_crotch_shelf_thickness_calibrated(preset: str) -> None:
    """TK-102: ``m`` middle shelf reads as solid ink (B-09), not a hairline."""
    ctx = getattr(DesignContext, preset)()
    glyph = Controls.from_context(ctx).build("m")
    ratio = m_crotch_shelf_thickness_over_stem(glyph)
    assert ratio >= M_CROTCH_SHELF_MIN_OVER_STEM


def test_m_crotch_shelf_min_ratio_frozen() -> None:
    assert M_CROTCH_SHELF_MIN_OVER_STEM == 0.28


def test_thickness_outlier_factor_frozen() -> None:
    assert THICKNESS_OUTLIER_FACTOR == 1.15


def test_hook_min_thin_ratio_tiers_frozen() -> None:
    assert HOOK_MIN_THIN_RATIO == 0.26
    assert HOOK_MIN_THIN_RATIO_SOFT == 0.22
    assert HOOK_MIN_THIN_RATIO_DISPLAY == 0.19


@pytest.mark.parametrize("char", ("f", "t", "g", "J", "j"))
def test_hook_root_thickness_humanist(char: str) -> None:
    ctx = DesignContext.humanist_sans()
    glyphs = Controls.from_context(ctx).build_all(char)
    glyph = glyphs[char]
    if char == "j":
        glyph = ComposedGlyph((glyph.solids[0],), (), glyph.advance, ctx)
    floor = hook_min_thin_floor(ctx)
    assert min_hook_thickness(glyph, char, ctx) >= floor


@pytest.mark.parametrize(
    "preset",
    ("code_clear", "geometric_sans", "open_print"),
)
def test_hook_root_thickness_roundness_tiers(preset: str) -> None:
    ctx = getattr(DesignContext, preset)()
    controls = Controls.from_context(ctx)
    floor = hook_min_thin_floor(ctx)
    for char in "ftgJ":
        glyph = controls.build(char)
        assert min_hook_thickness(glyph, char, ctx) >= floor
    j = controls.build("j")
    body = ComposedGlyph((j.solids[0],), (), j.advance, ctx)
    assert min_hook_thickness(body, "j", ctx) >= floor

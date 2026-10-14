"""Local thickness metric calibration (TK-102 fixtures)."""

from __future__ import annotations

import pytest

from typekernel.parts import Controls, DesignContext
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.primitives import vertical_stem
from typekernel.qa.lint import lint_controls
from typekernel.qa.thickness import (
    HOOK_MIN_THIN_RATIO,
    THICKNESS_OUTLIER_FACTOR,
    max_local_thickness,
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
        ("humanist_sans", 1.05),
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


def test_vertical_stem_measures_stem_width() -> None:
    ctx = DesignContext.code_clear()
    glyph = _stem_rect_glyph(ctx)
    measured = max_local_thickness(glyph)
    assert abs(measured - ctx.stem) <= ctx.stem * _STEM_TOLERANCE


def test_m_thickness_outlier_warns() -> None:
    controls = Controls.from_context(DesignContext.humanist_sans())
    report = lint_controls(controls, "mn", thickness=True)
    rules = {(i.glyph, i.rule) for i in report.issues}
    assert ("m", "R9_thickness_outlier") in rules
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

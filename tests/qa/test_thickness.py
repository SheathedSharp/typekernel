"""Local thickness metric calibration (TK-102 fixtures)."""

from __future__ import annotations

import pytest

from typekernel.parts import Controls, DesignContext
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.primitives import vertical_stem
from typekernel.qa.thickness import max_local_thickness, thickness_ratio_to_stem

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

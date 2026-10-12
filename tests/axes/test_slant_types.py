"""Tests for ObliqueTransform vs ItalicDesign split."""

from __future__ import annotations

import math

import pytest

from tests.axes._rect_helpers import closed_rect
from typekernel.axes import slant
from typekernel.axes.slant import ItalicDesign, ObliqueTransform


def test_oblique_transform_shears_x_with_y() -> None:
    outline = closed_rect(0, 0, 100, 200)
    angled = ObliqueTransform(angle_degrees=15.0).apply(outline)
    shear = math.tan(math.radians(15.0))
    tops = [pt for seg in angled.iter_segments() for pt in seg.points if pt.y == 200.0]
    assert tops
    xs_at_top = sorted({pt.x for pt in tops})
    assert xs_at_top[0] == pytest.approx(0.0 + 200.0 * shear)
    assert xs_at_top[-1] == pytest.approx(100.0 + 200.0 * shear)


def test_italic_design_raises() -> None:
    outline = closed_rect(0, 0, 1, 1)
    with pytest.raises(NotImplementedError, match="designed masters"):
        ItalicDesign().apply(outline)


def test_no_public_italic_shear_symbol() -> None:
    public = {name for name in dir(slant) if not name.startswith("_")}
    assert "italic_shear" not in public
    assert "ObliqueTransform" in public
    assert "ItalicDesign" in public

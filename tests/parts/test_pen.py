"""Parts wrappers for pen expand."""

from __future__ import annotations

import pytest

from typekernel.optics.stem import measure_oriented_stem
from typekernel.parts import DesignContext, expand_polyline, pen_from_context


def test_pen_from_context_uses_stem_and_contrast() -> None:
    ctx = DesignContext.geometric_sans().tuned(stem=70.0, contrast=0.6)
    pen = pen_from_context(ctx)
    assert pen.thickness == 70.0
    assert pen.contrast == 0.6


def test_expand_polyline_locks_contrast_widths() -> None:
    ctx = DesignContext.geometric_sans().tuned(stem=80.0, contrast=0.5)
    vert = expand_polyline([(50.0, 0.0), (50.0, 200.0)], ctx, cap="butt")
    horiz = expand_polyline([(0.0, 100.0), (200.0, 100.0)], ctx, cap="butt")
    assert measure_oriented_stem(vert, (50.0, 100.0), 90.0) == pytest.approx(80.0, abs=0.5)
    assert measure_oriented_stem(horiz, (100.0, 100.0), 0.0) == pytest.approx(40.0, abs=0.5)

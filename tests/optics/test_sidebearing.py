"""Tests for sidebearing suggestions."""

from __future__ import annotations

from typekernel.geo.path_builder import PathBuilder
from typekernel.optics.context import OpticalContext
from typekernel.optics.sidebearing import suggest_sidebearings


def test_suggest_sidebearings_scales_with_width() -> None:
    def box(w: float):
        b = PathBuilder()
        b.moveTo(0, 0)
        b.lineTo(w, 0)
        b.lineTo(w, 100)
        b.lineTo(0, 100)
        b.closePath()
        return b.build()

    ctx = OpticalContext.latin_defaults()
    narrow = suggest_sidebearings(box(80), ctx)
    wide = suggest_sidebearings(box(600), ctx)
    assert narrow[0] == narrow[1]
    assert narrow[0] > wide[0]

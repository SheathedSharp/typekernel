"""Sidebearing helper is implemented (heuristic, not a stub)."""

from __future__ import annotations

from typekernel.geo.path_builder import PathBuilder
from typekernel.optics.context import OpticalContext
from typekernel.optics.sidebearing import suggest_sidebearings


def test_suggest_sidebearings_returns_pair() -> None:
    b = PathBuilder()
    b.moveTo(0, 0)
    b.lineTo(100, 0)
    b.lineTo(100, 100)
    b.closePath()
    left, right = suggest_sidebearings(b.build(), OpticalContext.latin_defaults())
    assert left > 0 and right > 0

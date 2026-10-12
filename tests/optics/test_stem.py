"""Tests for vertical stem measurement."""

from pathlib import Path

from typekernel.geo.fixtures import load_synthetic_outline
from typekernel.optics.stem import measure_vertical_stem

FIXTURE = Path(__file__).parent.parent / "fixtures" / "synthetic_H.json"
STEM_WIDTH = 80.0
TOL = 0.5


def test_left_stem_width() -> None:
    outline = load_synthetic_outline(FIXTURE)
    width = measure_vertical_stem(outline, x=140.0)
    assert width is not None
    assert abs(width - STEM_WIDTH) <= TOL


def test_right_stem_width() -> None:
    outline = load_synthetic_outline(FIXTURE)
    width = measure_vertical_stem(outline, x=460.0)
    assert width is not None
    assert abs(width - STEM_WIDTH) <= TOL


def test_gap_between_stems_is_not_a_stem() -> None:
    outline = load_synthetic_outline(FIXTURE)
    assert measure_vertical_stem(outline, x=300.0) is None

"""check_drawing_interpolatable for Drawing masters."""

from __future__ import annotations

from typekernel.axes import GlyphMasters, check_drawing_interpolatable
from typekernel.draw import Writer


def _box(w: float, h: float = 100.0):
    return (
        Writer()
        .start((0.0, 0.0))
        .line((w, 0.0))
        .line((w, h))
        .line((0.0, h))
        .close()
        .build()
    )


def test_matching_signatures_ok() -> None:
    a = _box(80)
    b = _box(120)
    assert check_drawing_interpolatable([a, b]) == []


def test_mismatched_structure_reported() -> None:
    a = _box(80)
    # Extra contour → signature and contour count differ.
    b = a + _box(40)
    problems = check_drawing_interpolatable([a, b])
    assert problems
    assert any("signature" in p or "contour count" in p for p in problems)


def test_glyph_masters_add_drawing() -> None:
    masters = GlyphMasters()
    masters.add_drawing({"wght": 400}, _box(80))
    masters.add_drawing({"wght": 700}, _box(120))
    assert len(masters) == 2
    assert masters.get({"wght": 400}).contour_count == 1

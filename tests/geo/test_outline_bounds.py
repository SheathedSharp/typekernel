"""Unit tests for the outline bounds helper."""

from pathlib import Path

import pytest
from fontTools.pens.boundsPen import BoundsPen

from typekernel.geo.contour import Contour
from typekernel.geo.fixtures import load_synthetic_outline
from typekernel.geo.outline import Outline, bounds
from typekernel.geo.pens import draw_outline
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment

FIXTURE = Path(__file__).parent.parent / "fixtures" / "synthetic_O.json"


def _square(size: float = 10.0) -> Outline:
    a, b, c, d = (
        Point(0.0, 0.0),
        Point(size, 0.0),
        Point(size, size),
        Point(0.0, size),
    )
    return Outline(
        (
            Contour(
                (
                    LineSegment(a, b),
                    LineSegment(b, c),
                    LineSegment(c, d),
                    LineSegment(d, a),
                ),
                closed=True,
            ),
        )
    )


def test_known_square_bounds() -> None:
    assert bounds(_square()) == (0.0, 0.0, 10.0, 10.0)


def test_empty_outline_has_no_bounds() -> None:
    with pytest.raises(ValueError, match="no bounds"):
        bounds(Outline(()))


def test_outline_of_empty_contours_has_no_bounds() -> None:
    with pytest.raises(ValueError, match="no bounds"):
        bounds(Outline((Contour((), closed=True),)))


def test_synthetic_o_control_bounds() -> None:
    """The outer circle is tangent to y=0 and reaches y=700, x from 150 to 850."""
    assert bounds(load_synthetic_outline(FIXTURE)) == (150.0, 0.0, 850.0, 700.0)


def test_control_bounds_are_not_claimed_to_be_tight() -> None:
    """Documented v0 caveat: controls can lie outside the curve, so the box
    contains the shape but may be larger than the tight Bézier bounds."""
    bulging = Outline(
        (
            Contour(
                (
                    CubicSegment(
                        Point(0.0, 0.0),
                        Point(0.0, 100.0),
                        Point(100.0, 100.0),
                        Point(100.0, 0.0),
                    ),
                ),
                closed=False,
            ),
        )
    )
    min_x, min_y, max_x, max_y = bounds(bulging)
    assert (min_x, min_y, max_x, max_y) == (0.0, 0.0, 100.0, 100.0)

    pen = BoundsPen(None)
    draw_outline(bulging, pen)
    tight = pen.bounds
    assert tight is not None
    # The control box is at least as large as the tight one, in this case larger.
    assert max_y >= tight[3]
    assert max_y > tight[3]


def test_bounds_cover_every_contour() -> None:
    outline = Outline(
        (
            Contour((LineSegment(Point(0, 0), Point(1, 1)),), closed=False),
            Contour((LineSegment(Point(-5, -5), Point(2, 2)),), closed=False),
        )
    )
    assert bounds(outline) == (-5.0, -5.0, 2.0, 2.0)

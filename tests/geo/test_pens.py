"""Unit tests for the Outline → fontTools pen bridge."""

from fontTools.pens.recordingPen import RecordingPen

from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline
from typekernel.geo.pens import draw_outline
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment

A = Point(0.0, 0.0)
B = Point(10.0, 0.0)
C = Point(10.0, 10.0)


def _ops(outline: Outline) -> list[str]:
    pen = RecordingPen()
    draw_outline(outline, pen)
    return [op for op, _ in pen.value]


def test_cubic_input_emits_curve_to() -> None:
    outline = Outline((Contour((CubicSegment(A, B, C, A),), closed=True),))
    assert _ops(outline) == ["moveTo", "curveTo", "closePath"]


def test_cubic_is_never_silently_flattened_to_lines() -> None:
    """The whole point of the bridge: a curve must not come out as lines."""
    outline = Outline((Contour((CubicSegment(A, B, C, A),), closed=True),))
    ops = _ops(outline)
    assert "curveTo" in ops
    assert "lineTo" not in ops


def test_line_input_emits_line_to() -> None:
    outline = Outline(
        (Contour((LineSegment(A, B), LineSegment(B, C)), closed=True),)
    )
    assert _ops(outline) == ["moveTo", "lineTo", "lineTo", "closePath"]


def test_recorded_coordinates_are_passed_through_verbatim() -> None:
    cubic = CubicSegment(A, B, C, Point(0.0, 10.0))
    pen = RecordingPen()
    draw_outline(Outline((Contour((cubic,), closed=True),)), pen)
    assert pen.value == [
        ("moveTo", ((0.0, 0.0),)),
        ("curveTo", ((10.0, 0.0), (10.0, 10.0), (0.0, 10.0))),
        ("closePath", ()),
    ]


def test_open_contour_is_ended_with_end_path() -> None:
    outline = Outline((Contour((LineSegment(A, B),), closed=False),))
    assert _ops(outline) == ["moveTo", "lineTo", "endPath"]


def test_empty_contours_are_skipped() -> None:
    outline = Outline((Contour((), closed=True), Contour((), closed=False)))
    assert _ops(outline) == []


def test_multiple_contours_are_drawn_in_order() -> None:
    outline = Outline(
        (
            Contour((LineSegment(A, B),), closed=True),
            Contour((CubicSegment(A, B, C, A),), closed=False),
        )
    )
    assert _ops(outline) == [
        "moveTo",
        "lineTo",
        "closePath",
        "moveTo",
        "curveTo",
        "endPath",
    ]

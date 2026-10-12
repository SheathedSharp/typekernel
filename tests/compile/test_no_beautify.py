"""Export must not silently move or round outline coordinates."""

from __future__ import annotations

from pathlib import Path

import pytest

ufoLib2 = pytest.importorskip("ufoLib2")

from typekernel.compile.ufo_export import write_outline_to_ufo
from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.segment import CubicSegment, LineSegment

# UFO float storage should match design floats exactly for these values.
TOLERANCE = 0.0


def _on_curve_points(outline: Outline) -> list[tuple[float, float]]:
    """Collect on-curve endpoints in draw order (start + each segment end)."""
    points: list[tuple[float, float]] = []
    for contour in outline.contours:
        if not contour.segments:
            continue
        first = contour.segments[0].points[0]
        points.append((first.x, first.y))
        for segment in contour.segments:
            end = segment.points[-1]
            points.append((end.x, end.y))
        if contour.closed and points and points[-1] == points[0]:
            # Closed contours often omit the repeated start in UFO storage.
            points.pop()
    return points


def _ufo_on_curve_points(glyph: object) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for contour in glyph:  # type: ignore[attr-defined]
        for point in contour:
            if point.type is not None:  # on-curve: line / curve / qcurve / move
                points.append((float(point.x), float(point.y)))
    return points


def _all_control_points(outline: Outline) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for segment in outline.iter_segments():
        if isinstance(segment, CubicSegment):
            points.append((segment.p1.x, segment.p1.y))
            points.append((segment.p2.x, segment.p2.y))
        elif isinstance(segment, LineSegment):
            pass
    return points


def test_export_preserves_known_coordinates(tmp_path: Path) -> None:
    builder = PathBuilder()
    builder.moveTo(12.5, 34.75)
    builder.lineTo(200.125, 34.75)
    builder.curveTo(220.0, 80.5, 180.25, 120.0, 12.5, 100.5)
    builder.closePath()
    outline = builder.build()

    before_on = _on_curve_points(outline)
    before_off = _all_control_points(outline)

    ufo_path = tmp_path / "NoBeautify.ufo"
    write_outline_to_ufo(outline, ufo_path, glyph_name="N")
    font = ufoLib2.Font.open(ufo_path)
    after_on = _ufo_on_curve_points(font["N"])

    assert len(after_on) == len(before_on)
    for expected, actual in zip(before_on, after_on, strict=True):
        assert abs(expected[0] - actual[0]) <= TOLERANCE
        assert abs(expected[1] - actual[1]) <= TOLERANCE

    # Off-curve controls must also appear unchanged among UFO points.
    all_ufo = [(float(p.x), float(p.y)) for c in font["N"] for p in c]
    for off in before_off:
        assert off in all_ufo

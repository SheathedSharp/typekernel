"""Synthetic fixtures for midline / contrast pen expand."""

from __future__ import annotations

import math

import pytest

from typekernel.geo.outline import bounds
from typekernel.geo.stroke import Centerline, Pen, expand
from typekernel.optics.stem import measure_oriented_stem, measure_vertical_stem


def test_pen_rejects_non_positive() -> None:
    with pytest.raises(ValueError):
        Pen(thickness=0.0)
    with pytest.raises(ValueError):
        Pen(thickness=10.0, contrast=0.0)


def test_constant_pen_vertical_width_locks() -> None:
    outline = expand([(40.0, 0.0), (40.0, 200.0)], Pen(thickness=80.0), cap="butt")
    w = measure_oriented_stem(outline, (40.0, 100.0), 90.0)
    assert w == pytest.approx(80.0, abs=0.5)
    assert measure_vertical_stem(outline, 40.0) == pytest.approx(80.0, abs=0.5)


def test_constant_pen_horizontal_width_locks() -> None:
    outline = expand([(0.0, 100.0), (200.0, 100.0)], Pen(thickness=80.0), cap="butt")
    w = measure_oriented_stem(outline, (100.0, 100.0), 0.0)
    assert w == pytest.approx(80.0, abs=0.5)


def test_contrast_pen_horizontal_is_thinner() -> None:
    pen = Pen(thickness=80.0, contrast=0.5)
    outline = expand([(0.0, 100.0), (200.0, 100.0)], pen, cap="butt")
    w = measure_oriented_stem(outline, (100.0, 100.0), 0.0)
    assert w == pytest.approx(40.0, abs=0.5)
    # vertical still full thickness
    vert = expand([(40.0, 0.0), (40.0, 200.0)], pen, cap="butt")
    assert measure_oriented_stem(vert, (40.0, 100.0), 90.0) == pytest.approx(80.0, abs=0.5)


def test_contrast_pen_diagonal_matches_support() -> None:
    pen = Pen(thickness=80.0, contrast=0.5)
    outline = expand([(0.0, 0.0), (200.0, 200.0)], pen, cap="butt")
    nx, ny = -math.sqrt(0.5), math.sqrt(0.5)
    expected = 2.0 * pen.half_width(nx, ny)
    w = measure_oriented_stem(outline, (100.0, 100.0), 45.0)
    assert w == pytest.approx(expected, abs=0.8)
    assert expected == pytest.approx(math.sqrt(2.0 * (40.0**2 + 20.0**2)), abs=1e-6)


def test_square_cap_extends_by_half_width() -> None:
    butt = expand([(0.0, 0.0), (100.0, 0.0)], Pen(80.0), cap="butt")
    square = expand([(0.0, 0.0), (100.0, 0.0)], Pen(80.0), cap="square")
    bb_b = bounds(butt)
    bb_s = bounds(square)
    assert bb_b[0] == pytest.approx(0.0, abs=0.1)
    assert bb_b[2] == pytest.approx(100.0, abs=0.1)
    assert bb_s[0] == pytest.approx(-40.0, abs=0.5)
    assert bb_s[2] == pytest.approx(140.0, abs=0.5)


def test_round_cap_and_join_build() -> None:
    outline = expand(
        [(0.0, 0.0), (0.0, 100.0), (100.0, 100.0)],
        Pen(60.0),
        join="round",
        cap="round",
    )
    assert outline.contour_count == 1
    bb = bounds(outline)
    assert bb[2] > bb[0] and bb[3] > bb[1]


def test_bevel_join_builds() -> None:
    outline = expand(
        [(0.0, 0.0), (0.0, 80.0), (80.0, 80.0)],
        Pen(40.0),
        join="bevel",
        cap="butt",
    )
    assert outline.contour_count == 1


def test_closed_centerline_is_annulus() -> None:
    cl = Centerline.from_points(
        [(30.0, 30.0), (90.0, 30.0), (90.0, 90.0), (30.0, 90.0)], closed=True
    )
    ring = expand(cl, Pen(thickness=20.0), join="miter")
    assert ring.contour_count == 2
    min_x, min_y, max_x, max_y = bounds(ring)
    assert min_x == pytest.approx(20.0, abs=0.5)
    assert max_x == pytest.approx(100.0, abs=0.5)
    assert min_y == pytest.approx(20.0, abs=0.5)
    assert max_y == pytest.approx(100.0, abs=0.5)


def test_expand_rejects_bad_styles() -> None:
    with pytest.raises(ValueError):
        expand([(0.0, 0.0), (1.0, 0.0)], Pen(10.0), join="spline")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        expand([(0.0, 0.0), (1.0, 0.0)], Pen(10.0), cap="arrow")  # type: ignore[arg-type]

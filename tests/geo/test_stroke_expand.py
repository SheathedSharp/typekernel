"""Synthetic fixtures for midline / contrast pen expand."""

from __future__ import annotations

import itertools
import math

import pytest

from typekernel.geo.outline import bounds
from typekernel.geo.stroke import (
    Centerline,
    CubicBezier,
    CubicCenterline,
    Pen,
    cubic_centerline_to_polyline,
    expand,
    expand_cubic,
    flatten_cubic_centerline,
    polyline_to_cubic_centerline,
    refit_outline_to_cubics,
)
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


def _square_cubic_centerline() -> CubicCenterline:
    return CubicCenterline.from_beziers(
        (
            CubicBezier.line((30.0, 30.0), (90.0, 30.0)),
            CubicBezier.line((90.0, 30.0), (90.0, 90.0)),
            CubicBezier.line((90.0, 90.0), (30.0, 90.0)),
            CubicBezier.line((30.0, 90.0), (30.0, 30.0)),
        ),
        closed=True,
    )


def test_expand_cubic_closed_square_annulus() -> None:
    cl = _square_cubic_centerline()
    ring, report = expand_cubic(cl, Pen(thickness=20.0), offset_fit_budget=1.0)
    assert report.max_chord_error == 0.0
    assert report.max_offset_fit_error <= 1.0
    assert ring.contour_count == 2
    min_x, min_y, max_x, max_y = bounds(ring)
    assert min_x == pytest.approx(20.0, abs=1.5)
    assert max_x == pytest.approx(100.0, abs=1.5)
    assert min_y == pytest.approx(20.0, abs=1.5)
    assert max_y == pytest.approx(100.0, abs=1.5)


def test_expand_cubic_closed_square_round_join_matches_polyline_bbox() -> None:
    cl = _square_cubic_centerline()
    pen = Pen(thickness=20.0)
    ring_c, report = expand_cubic(cl, pen, offset_fit_budget=1.0, join="round")
    assert report.max_chord_error == 0.0
    poly, _ = flatten_cubic_centerline(cl, chord_budget=0.01)
    ring_p = expand(poly, pen, join="round")
    bb_c = bounds(ring_c)
    bb_p = bounds(ring_p)
    for i in range(4):
        assert bb_c[i] == pytest.approx(bb_p[i], abs=1.5)


def test_expand_cubic_closed_square_matches_polyline_annulus_bbox() -> None:
    cl = _square_cubic_centerline()
    pen = Pen(thickness=20.0)
    ring_c, _ = expand_cubic(cl, pen, offset_fit_budget=1.0)
    poly, _ = flatten_cubic_centerline(cl, chord_budget=0.01)
    ring_p = expand(poly, pen, join="miter")
    bb_c = bounds(ring_c)
    bb_p = bounds(ring_p)
    for i in range(4):
        assert bb_c[i] == pytest.approx(bb_p[i], abs=0.5)


def test_cubic_centerline_to_polyline_matches_flatten() -> None:
    seg = CubicBezier.line((0.0, 0.0), (50.0, 0.0))
    cl = CubicCenterline.from_beziers([seg])
    poly = cubic_centerline_to_polyline(cl, chord_budget=0.5)
    flat, _ = flatten_cubic_centerline(cl, chord_budget=0.5)
    assert poly.points == flat.points
    assert poly.closed == flat.closed


def test_flatten_cubic_line_is_two_points() -> None:
    seg = CubicBezier.line((10.0, 20.0), (110.0, 20.0))
    cl = CubicCenterline.from_beziers([seg])
    poly, report = flatten_cubic_centerline(cl, chord_budget=0.5)
    assert poly.points == ((10.0, 20.0), (110.0, 20.0))
    assert report.max_chord_error == 0.0
    assert report.cubic_segment_count == 1


def test_cubic_centerline_to_polyline_l_shape() -> None:
    segs = (
        CubicBezier.line((0.0, 0.0), (100.0, 0.0)),
        CubicBezier.line((100.0, 0.0), (100.0, 100.0)),
    )
    poly = cubic_centerline_to_polyline(CubicCenterline.from_beziers(segs), chord_budget=0.1)
    assert len(poly.points) >= 3
    assert poly.points[0] == (0.0, 0.0)
    assert poly.points[-1] == (100.0, 100.0)


def test_expand_cubic_multi_segment_matches_polyline_bbox() -> None:
    segs = (
        CubicBezier.line((0.0, 0.0), (100.0, 0.0)),
        CubicBezier.line((100.0, 0.0), (100.0, 100.0)),
    )
    cl = CubicCenterline.from_beziers(segs)
    pen = Pen(thickness=40.0)
    cubic_outline, _ = expand_cubic(cl, pen, cap="butt", chord_budget=0.05)
    poly_outline = expand([(0.0, 0.0), (100.0, 0.0), (100.0, 100.0)], pen, cap="butt")
    bb_c = bounds(cubic_outline)
    bb_p = bounds(poly_outline)
    for i in range(4):
        assert bb_c[i] == pytest.approx(bb_p[i], abs=0.5)


def test_expand_cubic_open_multi_segment_matches_polyline_helper() -> None:
    segs = (
        CubicBezier.line((0.0, 0.0), (100.0, 0.0)),
        CubicBezier.line((100.0, 0.0), (100.0, 100.0)),
    )
    cl = CubicCenterline.from_beziers(segs)
    pen = Pen(thickness=40.0)
    budget = 0.05
    cubic_outline, _ = expand_cubic(
        cl, pen, cap="butt", chord_budget=budget, offset_fit_budget=0.0
    )
    poly_outline = expand(cubic_centerline_to_polyline(cl, budget), pen, cap="butt")
    bb_c = bounds(cubic_outline)
    bb_p = bounds(poly_outline)
    for i in range(4):
        assert bb_c[i] == pytest.approx(bb_p[i], abs=0.01)


def test_expand_cubic_multi_segment_open_uses_chord_flatten() -> None:
    segs = (
        CubicBezier.line((0.0, 0.0), (100.0, 0.0)),
        CubicBezier.line((100.0, 0.0), (100.0, 100.0)),
    )
    cl = CubicCenterline.from_beziers(segs)
    pen = Pen(thickness=40.0)
    _, report = expand_cubic(
        cl, pen, cap="butt", chord_budget=0.25, offset_fit_budget=0.0
    )
    assert report.max_chord_error <= 0.25
    assert report.polyline_vertex_count >= 3
    assert report.max_offset_fit_error == 0.0


def test_expand_cubic_multi_segment_open_offset_rail_fit() -> None:
    segs = (
        CubicBezier.line((0.0, 0.0), (100.0, 0.0)),
        CubicBezier.line((100.0, 0.0), (100.0, 100.0)),
    )
    cl = CubicCenterline.from_beziers(segs)
    pen = Pen(thickness=40.0)
    outline, report = expand_cubic(cl, pen, cap="butt")
    assert report.max_chord_error == 0.0
    assert report.max_offset_fit_error <= 0.75
    assert report.outline_cubic_segment_count >= 2
    poly_outline = expand([(0.0, 0.0), (100.0, 0.0), (100.0, 100.0)], pen, cap="butt")
    bb_c = bounds(outline)
    bb_p = bounds(poly_outline)
    for i in range(4):
        assert bb_c[i] == pytest.approx(bb_p[i], abs=0.5)


def test_expand_cubic_open_line_round_cap_matches_polyline_bbox() -> None:
    seg = CubicBezier.line((0.0, 0.0), (200.0, 0.0))
    cl = CubicCenterline.from_beziers([seg])
    pen = Pen(thickness=80.0)
    cubic_outline, report = expand_cubic(cl, pen, cap="round")
    line_outline = expand([(0.0, 0.0), (200.0, 0.0)], pen, cap="round")
    assert report.max_chord_error == 0.0
    assert report.outline_cubic_segment_count >= 2
    bb_c = bounds(cubic_outline)
    bb_l = bounds(line_outline)
    for i in range(4):
        assert bb_c[i] == pytest.approx(bb_l[i], abs=1.0)


def test_expand_cubic_open_l_shape_round_join_bbox() -> None:
    segs = (
        CubicBezier.line((0.0, 0.0), (100.0, 0.0)),
        CubicBezier.line((100.0, 0.0), (100.0, 100.0)),
    )
    cl = CubicCenterline.from_beziers(segs)
    pen = Pen(thickness=40.0)
    cubic_outline, _ = expand_cubic(cl, pen, cap="butt", join="round")
    poly_outline = expand(
        [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0)],
        pen,
        cap="butt",
        join="round",
    )
    bb_c = bounds(cubic_outline)
    bb_p = bounds(poly_outline)
    for i in range(4):
        assert bb_c[i] == pytest.approx(bb_p[i], abs=1.5)


def test_expand_cubic_line_matches_polyline_expand() -> None:
    seg = CubicBezier.line((0.0, 0.0), (200.0, 0.0))
    cl = CubicCenterline.from_beziers([seg])
    pen = Pen(thickness=80.0)
    cubic_outline, report = expand_cubic(cl, pen, cap="butt", chord_budget=0.25)
    line_outline = expand([(0.0, 0.0), (200.0, 0.0)], pen, cap="butt")
    assert report.max_chord_error == 0.0
    bb_c = bounds(cubic_outline)
    bb_l = bounds(line_outline)
    for i in range(4):
        assert bb_c[i] == pytest.approx(bb_l[i], abs=0.5)


def test_expand_cubic_single_segment_reports_offset_fit_error() -> None:
    k = 0.5522847498 * 100.0
    seg = CubicBezier((0.0, 0.0), (0.0, k), (100.0 - k, 100.0), (100.0, 100.0))
    cl = CubicCenterline.from_beziers([seg])
    outline, report = expand_cubic(cl, Pen(40.0), cap="butt", offset_fit_budget=0.75)
    assert report.max_chord_error == 0.0
    assert report.max_offset_fit_error <= 0.75
    assert report.outline_cubic_segment_count >= 2
    assert outline.contour_count == 1


def test_expand_cubic_curved_centerline_within_chord_budget() -> None:
    k = 0.5522847498 * 100.0
    seg = CubicBezier((0.0, 0.0), (0.0, k), (100.0 - k, 100.0), (100.0, 100.0))
    cl = CubicCenterline.from_beziers([seg])
    outline, report = expand_cubic(
        cl, Pen(40.0), cap="butt", offset_fit_budget=0.75
    )
    assert report.cubic_segment_count == 1
    assert report.max_offset_fit_error <= 0.75
    assert outline.contour_count == 1
    bb = bounds(outline)
    assert bb[2] - bb[0] > 80.0
    assert bb[3] - bb[1] > 80.0


def test_polyline_to_cubic_centerline_fits_dense_open_stroke() -> None:
    pts = [(float(i * 8.0), 40.0 * math.sin(i * 0.35)) for i in range(24)]
    cl = polyline_to_cubic_centerline(pts, closed=False, fit_budget=0.75)
    assert cl.segments
    outline, report = expand_cubic(cl, Pen(30.0), cap="butt", offset_fit_budget=0.75)
    assert outline.contours
    assert report.max_offset_fit_error <= 0.75 + 1e-6


def test_expand_rejects_bad_styles() -> None:
    with pytest.raises(ValueError):
        expand([(0.0, 0.0), (1.0, 0.0)], Pen(10.0), join="spline")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        expand([(0.0, 0.0), (1.0, 0.0)], Pen(10.0), cap="arrow")  # type: ignore[arg-type]


def test_polyline_to_cubic_centerline_fits_curve() -> None:
    # Dense samples along a quarter-circle-ish polyline.
    pts = [(100.0 * math.cos(t), 100.0 * math.sin(t)) for t in [i * math.pi / 40 for i in range(21)]]
    cubic = polyline_to_cubic_centerline(pts, fit_budget=1.0, corner_deg=40.0)
    assert len(cubic.segments) >= 1
    assert len(cubic.segments) < len(pts)


def test_polyline_expand_via_cubic_is_mostly_cubics() -> None:
    from typekernel.geo.segment import CubicSegment, LineSegment
    from typekernel.parts.context import DesignContext
    from typekernel.parts.skeleton import Skeleton, Stroke, trace_letter

    pts = [(0.0, 0.0), (40.0, 80.0), (120.0, 100.0), (200.0, 40.0)]
    # densify
    dense: list[tuple[float, float]] = []
    for a, b in itertools.pairwise(pts):
        for i in range(8):
            t = i / 8.0
            dense.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    dense.append(pts[-1])
    sk = Skeleton.of(Stroke.from_points("s", dense, join="round", cap="round"))
    g = trace_letter(sk, DesignContext.geometric_sans(), blend=False, heal=False, refit=False)
    # Pre-boolean cubic expand path: almost all cubics.
    o = g.solids[0]
    n_line = sum(1 for c in o.contours for s in c.segments if isinstance(s, LineSegment))
    n_cub = sum(1 for c in o.contours for s in c.segments if isinstance(s, CubicSegment))
    assert n_cub > n_line
    assert n_cub >= 4


def test_refit_outline_to_cubics_after_union() -> None:
    from typekernel.geo.boolean import union_all
    from typekernel.geo.segment import CubicSegment, LineSegment

    a = expand([(0.0, 0.0), (0.0, 200.0)], Pen(60.0), join="round", cap="round")
    b = expand([(0.0, 100.0), (180.0, 100.0)], Pen(50.0), join="round", cap="round")
    merged = union_all([a, b])
    fitted = refit_outline_to_cubics(merged, fit_budget=2.5, corner_deg=35.0, min_step=2.5)
    n_line = sum(1 for c in fitted.contours for s in c.segments if isinstance(s, LineSegment))
    n_cub = sum(1 for c in fitted.contours for s in c.segments if isinstance(s, CubicSegment))
    assert n_cub > 0
    assert n_line == 0
    # Refit should not explode segment count relative to a sane cubic outline.
    assert n_cub < 200

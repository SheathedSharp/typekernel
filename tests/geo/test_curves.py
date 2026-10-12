"""Synthetic fixtures for superellipse and tension / bias cubics."""

from __future__ import annotations

import math

import pytest

from typekernel.geo.curves import (
    quarter_superellipse_cubics,
    superellipse,
    superellipse_kappa,
    superellipse_outline,
    tensioned_cubic,
    tune_contour_handles,
    tune_handles,
)
from typekernel.geo.outline import bounds
from typekernel.geo.path_helpers import KAPPA
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment


def _cubic_eval(seg: CubicSegment, t: float) -> tuple[float, float]:
    p0, p1, p2, p3 = seg.p0, seg.p1, seg.p2, seg.p3
    mt = 1.0 - t
    x = mt**3 * p0.x + 3 * mt * mt * t * p1.x + 3 * mt * t * t * p2.x + t**3 * p3.x
    y = mt**3 * p0.y + 3 * mt * mt * t * p1.y + 3 * mt * t * t * p2.y + t**3 * p3.y
    return (x, y)


def test_superellipse_kappa_matches_ellipse_at_n2() -> None:
    assert superellipse_kappa(2.0) == pytest.approx(KAPPA)


def test_superellipse_kappa_diamond_and_square_limits() -> None:
    assert superellipse_kappa(1.0) == pytest.approx(0.0)
    assert superellipse_kappa(1e9) == pytest.approx(4.0 / 3.0, abs=1e-6)


def test_superellipse_kappa_rejects_non_positive() -> None:
    with pytest.raises(ValueError):
        superellipse_kappa(0.0)


def test_n2_matches_ellipse_midpoint() -> None:
    p0, p1, p2, p3 = quarter_superellipse_cubics(0, 0, 100, 100, 0, n=2.0)
    seg = CubicSegment(p0, p1, p2, p3)
    x, y = _cubic_eval(seg, 0.5)
    target = 100.0 * math.sqrt(0.5)
    assert x == pytest.approx(target, abs=1e-6)
    assert y == pytest.approx(target, abs=1e-6)


def test_superellipse_n_gt2_is_squarer_than_ellipse() -> None:
    """At 45° sample, |x| is larger for n>2 (closer to the corner box)."""
    e = quarter_superellipse_cubics(0, 0, 100, 100, 0, n=2.0)
    s = quarter_superellipse_cubics(0, 0, 100, 100, 0, n=4.0)
    xe, _ = _cubic_eval(CubicSegment(*e), 0.5)
    xs, _ = _cubic_eval(CubicSegment(*s), 0.5)
    # n=4 mid target 2^(-1/4)≈0.841 > 0.707
    assert xs > xe + 5.0
    assert xs == pytest.approx(100.0 * (2.0 ** (-0.25)), abs=1e-5)


def test_superellipse_contour_closed_four_cubics() -> None:
    c = superellipse(50, 40, 30, 20, n=2.5, tension=1.0)
    assert c.closed
    assert len(c.segments) == 4
    assert all(isinstance(s, CubicSegment) for s in c.segments)


def test_superellipse_outline_bounds() -> None:
    o = superellipse_outline(0, 0, 80, 60, n=2.0)
    min_x, min_y, max_x, max_y = bounds(o)
    assert min_x == pytest.approx(-80.0, abs=0.01)
    assert max_x == pytest.approx(80.0, abs=0.01)
    assert min_y == pytest.approx(-60.0, abs=0.01)
    assert max_y == pytest.approx(60.0, abs=0.01)


def test_tension_scales_superellipse_handles() -> None:
    loose = quarter_superellipse_cubics(0, 0, 100, 100, 0, n=2.0, tension=0.5)
    tight = quarter_superellipse_cubics(0, 0, 100, 100, 0, n=2.0, tension=1.5)
    # p1.y - p0.y is the vertical handle length
    assert (loose[1].y - loose[0].y) == pytest.approx(0.5 * KAPPA * 100)
    assert (tight[1].y - tight[0].y) == pytest.approx(1.5 * KAPPA * 100)


def test_tune_handles_identity_and_collapse() -> None:
    seg = CubicSegment(Point(0, 0), Point(30, 0), Point(70, 0), Point(100, 0))
    assert tune_handles(seg, 1.0) is seg
    flat = tune_handles(seg, 0.0)
    assert flat.p1 == Point(0, 0)
    assert flat.p2 == Point(100, 0)


def test_tune_handles_bias_skews_lengths() -> None:
    seg = CubicSegment(Point(0, 0), Point(40, 0), Point(60, 0), Point(100, 0))
    skewed = tune_handles(seg, 1.0, bias=0.5)
    # outgoing shortened (1-0.5)=0.5 → p1 at 20; incoming lengthened (1.5) → p2 at 40 from end
    assert skewed.p1.x == pytest.approx(20.0)
    assert skewed.p2.x == pytest.approx(100.0 + (60.0 - 100.0) * 1.5)


def test_tensioned_cubic_and_contour_tune() -> None:
    seg = tensioned_cubic(
        Point(0, 0), Point(100, 0), Point(1, 0), Point(1, 0), tension=1.0, bias=0.0
    )
    assert seg.p1.x == pytest.approx(100.0 / 3.0)
    assert seg.p2.x == pytest.approx(200.0 / 3.0)
    c = superellipse(0, 0, 50, 50, n=2.0)
    tuned = tune_contour_handles(c, 0.5)
    assert len(tuned.segments) == 4
    s0 = tuned.segments[0]
    assert isinstance(s0, CubicSegment)
    assert (s0.p1.y - s0.p0.y) == pytest.approx(0.5 * KAPPA * 50)

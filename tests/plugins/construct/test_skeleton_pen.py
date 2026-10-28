"""Contract tests for ``plugins.construct.skeleton_pen`` (ARCHITECTURE.md「构造插件」)."""

from __future__ import annotations

import math

import pytest

from typekernel.geo.contour import signed_area
from typekernel.geo.stroke import Centerline, CubicBezier, CubicCenterline
from typekernel.plugins.construct import (
    broad_nib,
    densify_polyline,
    ellipse_point_count,
    expand_skeleton,
    expand_skeleton_cubic,
    pointed_pen,
)


def test_broad_nib_and_pointed_pen_factories() -> None:
    broad = broad_nib(80.0, contrast=0.5, angle_deg=25.0)
    pointed = pointed_pen(40.0)
    assert broad.thickness == 80.0
    assert broad.contrast == 0.5
    assert pointed.contrast == 1.0


def test_expand_open_stem_single_ink_contour() -> None:
    pen = broad_nib(60.0, contrast=0.55, angle_deg=20.0)
    cl = Centerline.from_points([(100.0, 0.0), (100.0, 500.0), (280.0, 500.0), (280.0, 0.0)])
    drawing = expand_skeleton(cl, pen, join="round", cap="round")
    assert len(drawing.contours) == 1
    assert drawing.roles == ("ink",)
    assert drawing.contours[0].closed
    assert signed_area(drawing.contours[0]) > 0.0
    assert drawing.slots == ()
    assert drawing.nodes == ((),)


def test_expand_closed_ring_ink_and_counter() -> None:
    pen = broad_nib(70.0, contrast=0.55, angle_deg=25.0)
    pts = [
        (250.0 + 180.0 * math.cos(2.0 * math.pi * i / 24.0), 260.0 + 200.0 * math.sin(2.0 * math.pi * i / 24.0))
        for i in range(24)
    ]
    drawing = expand_skeleton(Centerline.from_points(pts, closed=True), pen, join="bevel")
    assert len(drawing.contours) == 2
    assert set(drawing.roles) == {"ink", "counter"}
    ink = drawing.contours[drawing.roles.index("ink")]
    counter = drawing.contours[drawing.roles.index("counter")]
    assert signed_area(ink) > 0.0
    assert signed_area(counter) < 0.0


def test_expand_skeleton_cubic_returns_report() -> None:
    pen = pointed_pen(50.0)
    segs = (
        CubicBezier.line((120.0, 0.0), (120.0, 400.0)),
        CubicBezier((120.0, 400.0), (120.0, 480.0), (180.0, 520.0), (240.0, 520.0)),
        CubicBezier.line((240.0, 520.0), (320.0, 520.0)),
    )
    drawing, report = expand_skeleton_cubic(
        CubicCenterline.from_beziers(segs),
        pen,
        join="round",
        cap="round",
    )
    assert drawing.contours
    assert drawing.roles[0] == "ink"
    assert report.cubic_segment_count == 3


def test_expand_deterministic() -> None:
    pen = broad_nib(55.0, angle_deg=15.0)
    pts = [(80.0, 0.0), (80.0, 400.0), (200.0, 400.0), (200.0, 0.0)]
    a = expand_skeleton(pts, pen)
    b = expand_skeleton(pts, pen)
    assert tuple(type(s).__name__ for s in a.contours[0].segments) == tuple(
        type(s).__name__ for s in b.contours[0].segments
    )
    assert len(a.contours[0].segments) == len(b.contours[0].segments)


@pytest.mark.parametrize("thickness", [40.0, 70.0, 110.0])
def test_expand_over_thicknesses(thickness: float) -> None:
    pen = broad_nib(thickness, contrast=0.6, angle_deg=18.0)
    drawing = expand_skeleton(
        Centerline.from_points([(100.0, 0.0), (100.0, 500.0)]),
        pen,
        join="round",
        cap="round",
    )
    assert drawing.contours[0].closed
    assert signed_area(drawing.contours[0]) > 0.0


def test_expand_signature_stable_across_thickness() -> None:
    """Closed oval expand must keep Drawing.signature across pen weight (VF)."""
    pts = [
        (250.0 + 150.0 * math.cos(2.0 * math.pi * i / 28.0), 260.0 + 200.0 * math.sin(2.0 * math.pi * i / 28.0))
        for i in range(28)
    ]
    cl = Centerline.from_points(pts, closed=True)
    sigs = []
    for thickness in (44.0, 72.0, 100.0):
        pen = broad_nib(thickness, contrast=0.52, angle_deg=28.0)
        drawing = expand_skeleton(cl, pen, join="bevel", cap="round")
        # All segments promoted to cubics for master-compat.
        assert all(seg.kind == "cubic" for c in drawing.contours for seg in c.segments)
        sigs.append(drawing.signature())
    assert sigs[0] == sigs[1] == sigs[2]



def test_ellipse_point_count_grows_with_radius() -> None:
    small = ellipse_point_count(40, 40, chord_budget=0.5)
    big = ellipse_point_count(400, 400, chord_budget=0.5)
    assert big > small
    assert small >= 24


def test_densify_polyline_shortens_chords() -> None:
    pts = [
        (100.0 + 80.0 * math.cos(2.0 * math.pi * i / 12.0), 100.0 + 80.0 * math.sin(2.0 * math.pi * i / 12.0))
        for i in range(12)
    ]
    dense = densify_polyline(pts, closed=True, chord_budget=2.0)
    assert len(dense) > len(pts)


def test_expand_skeleton_densify_opt_in_stable_on_fixed_path() -> None:
    """Same centerline + same chord_budget → same signature across weights."""
    pts = [
        (250.0 + 150.0 * math.cos(2.0 * math.pi * i / 16.0), 260.0 + 200.0 * math.sin(2.0 * math.pi * i / 16.0))
        for i in range(16)
    ]
    cl = Centerline.from_points(pts, closed=True)
    sigs = []
    for thickness in (44.0, 100.0):
        pen = broad_nib(thickness, contrast=0.52, angle_deg=28.0)
        drawing = expand_skeleton(
            cl, pen, join="bevel", cap="round", chord_budget=2.0
        )
        sigs.append(drawing.signature())
    assert sigs[0] == sigs[1]


def test_expand_closed_round_join_fails_loud() -> None:
    """Closed + round must raise (VF signature flip); do not rely on comments."""
    pen = broad_nib(70.0, contrast=0.55, angle_deg=25.0)
    pts = [
        (250.0 + 180.0 * math.cos(2.0 * math.pi * i / 24.0), 260.0 + 200.0 * math.sin(2.0 * math.pi * i / 24.0))
        for i in range(24)
    ]
    with pytest.raises(ValueError, match="join='round'"):
        expand_skeleton(Centerline.from_points(pts, closed=True), pen, join="round")


def test_expand_closed_undersampled_raises_without_densify() -> None:
    pen = broad_nib(60.0, contrast=0.5, angle_deg=20.0)
    # 8-gon around a *large* oval — below ellipse_point_count(..., chord_budget=2).
    # Small dots / diamonds (n<8 or radius<60) are intentional polygons and pass.
    pts = [
        (250.0 + 200.0 * math.cos(2.0 * math.pi * i / 8.0), 260.0 + 220.0 * math.sin(2.0 * math.pi * i / 8.0))
        for i in range(8)
    ]
    with pytest.raises(ValueError, match="samples"):
        expand_skeleton(Centerline.from_points(pts, closed=True), pen, join="bevel")


def test_expand_closed_small_diamond_allowed() -> None:
    """i/j-style diamond dots must not trip the large-bowl sampling gate."""
    pen = broad_nib(40.0, contrast=0.5, angle_deg=20.0)
    pts = [(100.0, 80.0), (120.0, 100.0), (100.0, 120.0), (80.0, 100.0)]
    drawing = expand_skeleton(Centerline.from_points(pts, closed=True), pen, join="bevel")
    assert drawing.contours


def test_expand_chord_budget_auto_stable_across_thickness() -> None:
    """auto densify is centerline-only → same signature across pen weights."""
    pts = [
        (250.0 + 150.0 * math.cos(2.0 * math.pi * i / 16.0), 260.0 + 200.0 * math.sin(2.0 * math.pi * i / 16.0))
        for i in range(16)
    ]
    cl = Centerline.from_points(pts, closed=True)
    sigs = []
    for thickness in (44.0, 72.0, 100.0):
        pen = broad_nib(thickness, contrast=0.52, angle_deg=28.0)
        drawing = expand_skeleton(cl, pen, join="bevel", chord_budget="auto")
        sigs.append(drawing.signature())
    assert sigs[0] == sigs[1] == sigs[2]

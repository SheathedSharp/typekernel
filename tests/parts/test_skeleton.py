"""Synthetic fixtures for shape-agnostic skeleton → outline tracing."""

from __future__ import annotations

import importlib.util

import pytest

from typekernel.geo.joins import classify_joins
from typekernel.geo.outline import bounds
from typekernel.geo.stroke import CubicBezier
from typekernel.optics.stem import measure_oriented_stem, measure_vertical_stem
from typekernel.parts import (
    DesignContext,
    EndTreatment,
    Skeleton,
    Stroke,
    trace_letter,
)

HAS_PATHOPS = importlib.util.find_spec("pathops") is not None


def _h_skeleton(stem: float = 80.0) -> Skeleton:
    """Synthetic H: left stem, right stem, crossbar — named polylines."""
    return Skeleton.from_polylines(
        {
            "left": [(40.0, 0.0), (40.0, 400.0)],
            "right": [(240.0, 0.0), (240.0, 400.0)],
            "bar": [(40.0, 200.0), (240.0, 200.0)],
        },
        thickness=stem,
    )


def test_stroke_rejects_short_polyline() -> None:
    with pytest.raises(ValueError, match="at least two"):
        Stroke.from_points("x", [(0.0, 0.0)])


def test_stroke_allows_zero_offset_fit_budget() -> None:
    stroke = Stroke.from_beziers(
        "seg",
        (CubicBezier.line((0.0, 0.0), (120.0, 0.0)),),
        offset_fit_budget=0.0,
    )
    assert stroke.offset_fit_budget == 0.0


def test_stroke_rejects_negative_offset_fit_budget() -> None:
    with pytest.raises(ValueError, match="offset_fit_budget"):
        Stroke.from_beziers(
            "seg",
            (CubicBezier.line((0.0, 0.0), (10.0, 0.0)),),
            offset_fit_budget=-0.1,
        )


def test_skeleton_rejects_duplicate_names() -> None:
    a = Stroke.from_points("stem", [(0.0, 0.0), (0.0, 100.0)])
    b = Stroke.from_points("stem", [(50.0, 0.0), (50.0, 100.0)])
    with pytest.raises(ValueError, match="duplicate"):
        Skeleton.of(a, b)


def test_closed_cubic_stroke_expand_splits_annulus() -> None:
    from typekernel.geo.stroke import CubicBezier
    from typekernel.parts.skeleton import _expand_stroke

    square = (
        CubicBezier.line((30.0, 30.0), (90.0, 30.0)),
        CubicBezier.line((90.0, 30.0), (90.0, 90.0)),
        CubicBezier.line((90.0, 90.0), (30.0, 90.0)),
        CubicBezier.line((30.0, 90.0), (30.0, 30.0)),
    )
    stroke = Stroke.from_beziers(
        "ring",
        square,
        closed=True,
        thickness=20.0,
        chord_budget=0.35,
    )
    ctx = DesignContext.geometric_sans()
    solids, holes = _expand_stroke(
        stroke,
        ctx,
        default_join="miter",
        default_cap="butt",
        miter_limit=4.0,
    )
    assert len(solids) == 1 and len(holes) == 1
    bb = bounds(solids[0])
    assert bb[0] == pytest.approx(20.0, abs=2.0)
    assert bb[2] == pytest.approx(100.0, abs=2.0)


def test_trace_letter_cubic_stroke_matches_polyline_stem() -> None:
    ctx = DesignContext.geometric_sans().tuned(stem=80.0, contrast=1.0)
    poly = trace_letter(
        Skeleton.of(
            Stroke.from_points("stem", [(40.0, 0.0), (40.0, 400.0)], thickness=80.0)
        ),
        ctx,
        union=False,
        blend=False,
        ease=False,
        cap="butt",
    )
    cubic = trace_letter(
        Skeleton.of(
            Stroke.from_beziers(
                "stem",
                (CubicBezier.line((40.0, 0.0), (40.0, 400.0)),),
                thickness=80.0,
            )
        ),
        ctx,
        union=False,
        blend=False,
        ease=False,
        cap="butt",
    )
    bb_p = bounds(poly.solids[0])
    bb_c = bounds(cubic.solids[0])
    for i in range(4):
        assert bb_p[i] == pytest.approx(bb_c[i], abs=1.0)


def test_from_mapping_accepts_zero_offset_fit_budget() -> None:
    skel = Skeleton.from_mapping(
        {
            "seg": {
                "beziers": [
                    [(0.0, 0.0), (33.0, 0.0), (67.0, 0.0), (100.0, 0.0)],
                ],
                "offset_fit_budget": 0.0,
                "thickness": 20.0,
            },
        }
    )
    assert skel.strokes[0].offset_fit_budget == 0.0


def test_from_mapping_beziers_join_and_cap() -> None:
    skel = Skeleton.from_mapping(
        {
            "stem": {
                "beziers": [
                    [(40.0, 0.0), (40.0, 133.0), (40.0, 267.0), (40.0, 400.0)],
                ],
                "thickness": 80.0,
                "join": "miter",
                "cap": "butt",
            },
        }
    )
    stroke = skel.strokes[0]
    assert stroke.join == "miter"
    assert stroke.cap == "butt"


def test_from_mapping_accepts_cubic_beziers() -> None:
    skel = Skeleton.from_mapping(
        {
            "arc": {
                "beziers": [
                    [
                        (0.0, 0.0),
                        (0.0, 55.0),
                        (45.0, 100.0),
                        (100.0, 100.0),
                    ],
                ],
                "thickness": 30.0,
                "chord_budget": 0.3,
            },
        }
    )
    assert skel.strokes[0].beziers is not None
    assert skel.strokes[0].chord_budget == 0.3
    glyph = trace_letter(skel, DesignContext.geometric_sans(), union=False, blend=False)
    assert glyph.solids


def test_from_mapping_accepts_points_and_dict() -> None:
    skel = Skeleton.from_mapping(
        {
            "stem": [(0.0, 0.0), (0.0, 200.0)],
            "bowl": {
                "points": [(80.0, 40.0), (180.0, 40.0), (180.0, 160.0), (80.0, 160.0)],
                "closed": True,
                "thickness": 40.0,
            },
        }
    )
    assert [s.name for s in skel.strokes] == ["stem", "bowl"]
    assert skel.strokes[1].closed is True
    assert skel.strokes[1].thickness == 40.0


def test_trace_letter_h_locks_vertical_stem_width() -> None:
    """Per-stroke expand locks stem width (measure before junction union)."""
    ctx = DesignContext.geometric_sans().tuned(stem=80.0, contrast=1.0)
    glyph = trace_letter(
        _h_skeleton(80.0), ctx, union=False, blend=False, ease=False, cap="butt"
    )
    assert glyph.advance > 0
    assert len(glyph.solids) == 3
    left = glyph.solids[0]
    bb = bounds(left)
    cx = 0.5 * (bb[0] + bb[2])
    assert measure_vertical_stem(left, cx) == pytest.approx(80.0, abs=1.0)


def test_trace_letter_contrast_thins_crossbar() -> None:
    ctx = DesignContext.geometric_sans().tuned(stem=80.0, contrast=0.5)
    glyph = trace_letter(
        _h_skeleton(80.0), ctx, union=False, blend=False, ease=False, cap="butt"
    )
    bar = glyph.solids[2]
    bb = bounds(bar)
    mid = (0.5 * (bb[0] + bb[2]), 0.5 * (bb[1] + bb[3]))
    assert measure_oriented_stem(bar, mid, 0.0) == pytest.approx(40.0, abs=1.5)


@pytest.mark.skipif(not HAS_PATHOPS, reason="pathops required for union")
def test_trace_letter_union_merges_named_strokes() -> None:
    ctx = DesignContext.geometric_sans().tuned(stem=80.0)
    separate = trace_letter(
        _h_skeleton(), ctx, union=False, blend=False, ease=False, cap="butt"
    )
    merged = trace_letter(
        _h_skeleton(), ctx, union=True, blend=False, ease=False, cap="butt"
    )
    assert len(separate.solids) == 3
    assert len(merged.solids) == 1
    assert merged.advance == pytest.approx(separate.advance, abs=1.0)


@pytest.mark.skipif(not HAS_PATHOPS, reason="pathops required for closed subtract")
def test_trace_letter_closed_ring_has_counter() -> None:
    ctx = DesignContext.geometric_sans().tuned(stem=40.0)
    skel = Skeleton.from_polylines(
        {
            "ring": [
                (0.0, 0.0),
                (200.0, 0.0),
                (200.0, 200.0),
                (0.0, 200.0),
            ],
        },
        closed=["ring"],
        thickness=40.0,
    )
    glyph = trace_letter(skel, ctx, union=True, blend=False, ease=False, join="miter")
    body = glyph.solids[0]
    n_contours = sum(len(s.contours) for s in glyph.solids) + sum(
        len(h.contours) for h in glyph.holes
    )
    assert n_contours >= 2
    bb = bounds(body)
    assert bb[2] - bb[0] > 150
    assert bb[3] - bb[1] > 150


@pytest.mark.skipif(not HAS_PATHOPS, reason="pathops required for closed subtract")
def test_trace_letter_closed_cubic_ring_has_counter() -> None:
    ctx = DesignContext.geometric_sans().tuned(stem=40.0)
    ring = (
        CubicBezier.line((30.0, 30.0), (90.0, 30.0)),
        CubicBezier.line((90.0, 30.0), (90.0, 90.0)),
        CubicBezier.line((90.0, 90.0), (30.0, 90.0)),
        CubicBezier.line((30.0, 90.0), (30.0, 30.0)),
    )
    skel = Skeleton.of(
        Stroke.from_beziers("ring", ring, thickness=20.0, closed=True),
    )
    glyph = trace_letter(skel, ctx, union=True, blend=False, ease=False, join="miter")
    n_contours = sum(len(s.contours) for s in glyph.solids) + sum(
        len(h.contours) for h in glyph.holes
    )
    assert n_contours >= 2
    bb = bounds(glyph.solids[0])
    assert bb[2] - bb[0] > 40.0
    assert bb[3] - bb[1] > 40.0


@pytest.mark.skipif(not HAS_PATHOPS, reason="pathops required for closed subtract")
def test_trace_letter_closed_cubic_ring_matches_polyline_ring() -> None:
    ctx = DesignContext.geometric_sans().tuned(stem=40.0)
    square = (
        (30.0, 30.0),
        (90.0, 30.0),
        (90.0, 90.0),
        (30.0, 90.0),
    )
    ring = tuple(
        CubicBezier.line(square[i], square[(i + 1) % len(square)]) for i in range(len(square))
    )
    poly_skel = Skeleton.from_polylines(
        {"ring": square},
        closed=["ring"],
        thickness=20.0,
    )
    cubic_skel = Skeleton.of(
        Stroke.from_beziers("ring", ring, thickness=20.0, closed=True),
    )
    poly_glyph = trace_letter(
        poly_skel, ctx, union=True, blend=False, ease=False, join="miter"
    )
    cubic_glyph = trace_letter(
        cubic_skel, ctx, union=True, blend=False, ease=False, join="miter"
    )
    bb_p = bounds(poly_glyph.solids[0])
    bb_c = bounds(cubic_glyph.solids[0])
    for i in range(4):
        assert bb_c[i] == pytest.approx(bb_p[i], abs=3.0)


@pytest.mark.skipif(not HAS_PATHOPS, reason="pathops required for union+blend")
def test_trace_letter_blend_does_not_add_kinks() -> None:
    ctx = DesignContext.geometric_sans().tuned(stem=60.0, roundness=0.4)
    skel = Skeleton.of(
        Stroke.from_points("vert", [(50.0, 0.0), (50.0, 200.0)]),
        Stroke.from_points("horiz", [(50.0, 50.0), (200.0, 50.0)]),
    )
    raw = trace_letter(
        skel, ctx, union=True, blend=False, ease=False, join="miter", cap="butt"
    )
    blended = trace_letter(
        skel, ctx, union=True, blend=True, ease=False, join="miter", cap="butt"
    )
    assert classify_joins(blended.solids[0]).kinks <= classify_joins(raw.solids[0]).kinks
    assert ctx.join_radius == pytest.approx(24.0, abs=0.01)


@pytest.mark.skipif(not HAS_PATHOPS, reason="pathops for ball terminal")
def test_trace_letter_ball_terminal_grows_bbox() -> None:
    ctx = DesignContext.geometric_sans().tuned(stem=40.0)
    plain = Skeleton.of(
        Stroke.from_points("s", [(0.0, 100.0), (200.0, 100.0)], cap="butt")
    )
    balled = Skeleton.of(
        Stroke.from_points(
            "s",
            [(0.0, 100.0), (200.0, 100.0)],
            cap="butt",
            end=EndTreatment(kind="ball", size=30.0),
        )
    )
    g0 = trace_letter(plain, ctx, union=False, blend=False, ease=False, cap="butt")
    g1 = trace_letter(balled, ctx, union=False, blend=False, ease=False, cap="butt")
    b0 = bounds(g0.solids[0])
    b1 = bounds(g1.solids[0])
    assert b1[2] - b1[0] > b0[2] - b0[0]


def test_trace_letter_accepts_skeleton_dict() -> None:
    ctx = DesignContext.geometric_sans().tuned(stem=50.0)
    glyph = trace_letter(
        {"stem": [(10.0, 0.0), (10.0, 100.0)]},
        ctx,
        union=False,
        blend=False,
        ease=False,
        cap="butt",
    )
    assert glyph.advance > 0
    bb = bounds(glyph.solids[0])
    w = measure_vertical_stem(glyph.solids[0], 0.5 * (bb[0] + bb[2]))
    assert w == pytest.approx(50.0, abs=1.0)

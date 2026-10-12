"""Synthetic fixtures for shape-agnostic skeleton → outline tracing."""

from __future__ import annotations

import importlib.util

import pytest

from typekernel.geo.joins import classify_joins
from typekernel.geo.outline import bounds
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


def test_skeleton_rejects_duplicate_names() -> None:
    a = Stroke.from_points("stem", [(0.0, 0.0), (0.0, 100.0)])
    b = Stroke.from_points("stem", [(50.0, 0.0), (50.0, 100.0)])
    with pytest.raises(ValueError, match="duplicate"):
        Skeleton.of(a, b)


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

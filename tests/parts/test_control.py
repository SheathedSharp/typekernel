"""Control glyphs and related forms (designer workflow)."""

from __future__ import annotations

import importlib.util

import pytest

from typekernel.geo.contour import signed_area
from typekernel.geo.outline import bounds
from typekernel.geo.segment import CubicSegment
from typekernel.optics.stem import measure_vertical_stem
from typekernel.parts import (
    DesignContext,
    build_control_word,
    build_h,
    build_n,
    build_o,
    h_from_n,
    n_metrics,
    u_from_n,
)

HAS_PATHOPS = importlib.util.find_spec("pathops") is not None


def test_n_is_single_continuous_outline() -> None:
    ctx = DesignContext.code_clear()
    g = build_n(ctx)
    assert len(g.solids) == 1
    assert len(g.holes) == 0
    body = g.solids[0]
    assert len(body.contours) == 1
    assert signed_area(body.contours[0]) > 0
    n_cub = sum(1 for s in body.contours[0].segments if isinstance(s, CubicSegment))
    assert n_cub >= 4  # outer + inner shoulder


def test_n_and_h_share_metrics_shoulder() -> None:
    ctx = DesignContext.paper_ink()
    m = n_metrics(ctx)
    n = build_n(ctx)
    h = h_from_n(n)
    assert h_from_n(n).advance == pytest.approx(build_h(ctx).advance)
    # h taller (ascender); same advance rhythm
    assert bounds(h.solids[0])[3] == pytest.approx(ctx.ascender, abs=1.0)
    assert bounds(n.solids[0])[3] == pytest.approx(m.crown_y, abs=1.0)
    assert n.advance == pytest.approx(h.advance, abs=1.0)


def test_h_right_leg_does_not_stub_above_join() -> None:
    ctx = DesignContext.code_clear()
    m = n_metrics(ctx)
    # Leg top metric is at ~x-height; old CAD bug used 0.58*xh mid-stem meet.
    assert m.leg_top > ctx.x_height * 0.9
    g = build_h(ctx)
    assert g.advance > 0


def test_o_overshoot_and_cubics() -> None:
    pytest.importorskip("pathops")
    ctx = DesignContext.paper_ink()
    g = build_o(ctx)
    bb = bounds(g.solids[0])
    assert bb[1] < -ctx.overshoot * 0.3
    n_cub = sum(
        1
        for c in g.solids[0].contours
        for s in c.segments
        if isinstance(s, CubicSegment)
    )
    assert n_cub >= 4


def test_u_from_n_related() -> None:
    ctx = DesignContext.code_clear()
    n = build_n(ctx)
    u = u_from_n(n)
    assert u.advance == pytest.approx(n.advance, abs=2.0)


def test_n_stem_width() -> None:
    ctx = DesignContext.geometric_sans().tuned(stem=80.0)
    g = build_n(ctx)
    bb = bounds(g.solids[0])
    w = measure_vertical_stem(g.solids[0], bb[0] + 40.0)
    assert w == pytest.approx(80.0, abs=2.0)


def test_control_word_ohio() -> None:
    ctx = DesignContext.code_clear()
    glyphs = build_control_word("ohio", ctx)
    assert len(glyphs) == 4
    assert all(g.advance > 0 for g in glyphs)


def test_n_not_boolean_part_count() -> None:
    """Control n is one outline — not three unioned parts."""
    ctx = DesignContext.code_clear()
    g = build_n(ctx)
    assert len(g.solids) == 1
    # Few segments relative to bead-expand arches (was 80+)
    nseg = sum(len(c.segments) for c in g.solids[0].contours)
    assert nseg < 30

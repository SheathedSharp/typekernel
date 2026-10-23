"""b d p q derive from the o bowl and the n stem — no booleans."""

from __future__ import annotations

import pytest

from typekernel.axes.interpolatable import check_interpolatable
from typekernel.geo.contour import signed_area
from typekernel.geo.outline import bounds
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import (
    DesignContext,
    b_from_o,
    build_n,
    build_o,
    d_from_o,
    n_metrics,
    o_metrics,
    p_from_o,
    q_from_o,
)
from typekernel.parts.control import CONTROL_BUILDERS

DERIVE = {"b": b_from_o, "d": d_from_o, "p": p_from_o, "q": q_from_o}


@pytest.fixture
def ctx() -> DesignContext:
    return DesignContext.code_clear()


def _width(g) -> float:
    b = bounds(g.solids[0])
    return b[2] - b[0]


@pytest.mark.parametrize("letter", "bdpq")
def test_outer_ccw_counter_cw_and_stable_topology(ctx: DesignContext, letter: str) -> None:
    glyphs = [
        CONTROL_BUILDERS[letter](ctx.tuned(stem=s, roundness=r))
        for s, r in ((50, 0.1), (86, 0.3), (150, 0.6))
    ]
    for g in glyphs:
        outer, counter = g.solids[0].contours
        assert signed_area(outer) > 0 > signed_area(counter)
    assert check_interpolatable([g.solids[0] for g in glyphs]) == []


@pytest.mark.parametrize("letter", "bdpq")
def test_bowl_width_and_stem_from_controls(ctx: DesignContext, letter: str) -> None:
    n_m = n_metrics(ctx).tuned(stem=110.0)
    g = DERIVE[letter](build_o(ctx), build_n(ctx, n_m))
    assert _width(g) == pytest.approx(o_metrics(ctx).width)
    probe_y = ctx.ascender - 20 if letter in "bd" else ctx.descender + 20
    (interval,) = ink_intervals_at_y(list(g.solids), probe_y)
    assert interval[1] - interval[0] == pytest.approx(110.0, abs=0.01)


def test_vertical_extents(ctx: DesignContext) -> None:
    o, n = build_o(ctx), build_n(ctx)
    m = o_metrics(ctx)
    for letter in "bd":
        b = bounds(DERIVE[letter](o, n).solids[0])
        assert b[1] == pytest.approx(-m.overshoot)
        assert b[3] == pytest.approx(ctx.ascender)
    for letter in "pq":
        b = bounds(DERIVE[letter](o, n).solids[0])
        assert b[1] == pytest.approx(ctx.descender)
        assert b[3] == pytest.approx(ctx.x_height + m.overshoot)


def test_b_mirrors_d(ctx: DesignContext) -> None:
    o, n = build_o(ctx), build_n(ctx)
    b, d = b_from_o(o, n), d_from_o(o, n)
    assert _width(b) == pytest.approx(_width(d))
    assert signed_area(b.solids[0].contours[1]) == pytest.approx(
        signed_area(d.solids[0].contours[1])
    )
    # stem on opposite sides at ascender height
    (bi,) = ink_intervals_at_y(list(b.solids), ctx.ascender - 10)
    (di,) = ink_intervals_at_y(list(d.solids), ctx.ascender - 10)
    bb, db = bounds(b.solids[0]), bounds(d.solids[0])
    assert bi[0] == pytest.approx(bb[0])
    assert di[1] == pytest.approx(db[2])


def test_thinner_join_opens_counter(ctx: DesignContext) -> None:
    o, n = build_o(ctx), build_n(ctx)
    thin = d_from_o(o, n, join=0.6).solids[0].contours[1]
    full = d_from_o(o, n, join=1.0).solids[0].contours[1]
    assert abs(signed_area(thin)) > abs(signed_area(full))


def test_tuned_o_flows_into_d(ctx: DesignContext) -> None:
    wide = o_metrics(ctx).tuned(rx=o_metrics(ctx).rx + 40.0)
    d = d_from_o(build_o(ctx, wide), build_n(ctx))
    assert _width(d) == pytest.approx(wide.width)
    assert d.design == wide


def test_anchors(ctx: DesignContext) -> None:
    o, n = build_o(ctx), build_n(ctx)
    assert {a.name for a in d_from_o(o, n).anchors} == {"top", "bottom"}
    assert d_from_o(o, n).anchor("top").y == ctx.x_height
    assert {a.name for a in q_from_o(o, n).anchors} == {"top"}

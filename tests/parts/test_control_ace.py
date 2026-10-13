"""a c e derive from the o ring — fixed topology, no booleans."""

from __future__ import annotations

import pytest

from typekernel.geo.contour import signed_area
from typekernel.geo.outline import bounds
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import (
    DesignContext,
    a_from_o,
    build_n,
    build_o,
    c_from_o,
    e_from_o,
    n_metrics,
    o_metrics,
)


@pytest.fixture
def ctx() -> DesignContext:
    return DesignContext.code_clear()


def _box(g) -> tuple[float, float, float, float]:
    return bounds(g.solids[0])


def test_c_is_one_ccw_contour_narrower_than_o(ctx: DesignContext) -> None:
    o = build_o(ctx)
    c = c_from_o(o)
    (contour,) = c.solids[0].contours
    assert signed_area(contour) > 0
    assert _box(c)[2] - _box(c)[0] < o_metrics(ctx).width
    assert _box(c)[1] == pytest.approx(-ctx.overshoot)


def test_c_aperture_opens_toward_centre(ctx: DesignContext) -> None:
    o = build_o(ctx)
    closed, open_ = c_from_o(o, aperture=0.1), c_from_o(o, aperture=0.9)
    assert _box(open_)[2] - _box(open_)[0] < _box(closed)[2] - _box(closed)[0]
    # nothing at the right edge on the centre line: the aperture
    m = o_metrics(ctx)
    runs = ink_intervals_at_y(list(open_.solids), ctx.x_height / 2.0)
    assert len(runs) == 1 and runs[0][1] < m.width / 2.0


def test_e_bar_spans_and_aperture_opens(ctx: DesignContext) -> None:
    e = e_from_o(build_o(ctx))
    outer, eye = e.solids[0].contours
    assert signed_area(outer) > 0 > signed_area(eye)
    x0, _, x1, _ = _box(e)
    bar_t = o_metrics(ctx).thickness * ctx.contrast
    bar_y = ctx.x_height / 2.0 + 0.25 * bar_t
    (run,) = ink_intervals_at_y(list(e.solids), bar_y)
    assert run[0] == pytest.approx(x0, abs=0.5) and run[1] == pytest.approx(x1, abs=0.5)
    under = ink_intervals_at_y(list(e.solids), bar_y - bar_t / 2.0 - 4.0)
    assert max(r[1] for r in under) < x1 - o_metrics(ctx).thickness


def test_e_bar_raise_moves_bar(ctx: DesignContext) -> None:
    o = build_o(ctx)
    low = e_from_o(o, bar_raise=-0.3).solids[0].contours[1]
    high = e_from_o(o, bar_raise=0.4).solids[0].contours[1]
    assert abs(signed_area(high)) < abs(signed_area(low))


def test_a_stem_from_n_stops_at_x_height(ctx: DesignContext) -> None:
    n = build_n(ctx, n_metrics(ctx).tuned(stem=104.0))
    a = a_from_o(build_o(ctx), n)
    (run,) = ink_intervals_at_y(list(a.solids), 8.0)[-1:]
    assert run[1] - run[0] >= 104.0 - 0.01
    assert _box(a)[3] == pytest.approx(ctx.x_height + ctx.overshoot)
    assert {x.name for x in a.anchors} == {"top", "bottom", "ogonek"}


def test_tuned_o_flows_into_ace(ctx: DesignContext) -> None:
    wide = o_metrics(ctx).tuned(rx=o_metrics(ctx).rx + 30.0)
    base_o, wide_o = build_o(ctx), build_o(ctx, wide)
    for derive in (lambda o: c_from_o(o), lambda o: e_from_o(o)):
        assert (_box(derive(wide_o))[2] - _box(derive(wide_o))[0]) > (
            _box(derive(base_o))[2] - _box(derive(base_o))[0]
        )

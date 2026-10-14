"""m and r are cut from the n shoulder — no booleans, stable topology."""

from __future__ import annotations

import pytest

from typekernel.axes.interpolatable import check_interpolatable
from typekernel.geo.contour import signed_area
from typekernel.geo.outline import bounds
from typekernel.parts import DesignContext, build_n, n_metrics
from typekernel.parts.control import build_m, build_r, m_from_n, r_from_n


def _cubics_from_left(g) -> list[tuple[tuple[float, float], ...]]:
    x0 = bounds(g.solids[0])[0]
    return [
        tuple((round(p.x - x0, 6), round(p.y, 6)) for p in s.points)
        for s in g.solids[0].contours[0].segments
        if s.kind == "cubic"
    ]


@pytest.fixture
def ctx() -> DesignContext:
    return DesignContext.code_clear()


@pytest.mark.parametrize("builder", [build_m, build_r])
def test_single_ccw_contour_with_stable_topology(ctx: DesignContext, builder) -> None:
    glyphs = [builder(ctx.tuned(stem=s, roundness=r)) for s, r in ((50, 0.1), (86, 0.3), (140, 0.6))]
    for g in glyphs:
        assert len(g.solids) == 1 and len(g.solids[0].contours) == 1
        assert signed_area(g.solids[0].contours[0]) > 0
    assert check_interpolatable([g.solids[0] for g in glyphs]) == []


def test_r_arm_is_truncated_n_shoulder(ctx: DesignContext) -> None:
    n = build_n(ctx)
    r = r_from_n(n)
    assert _cubics_from_left(r)[0] == _cubics_from_left(n)[0]
    m = n_metrics(ctx)
    width = bounds(r.solids[0])[2] - bounds(r.solids[0])[0]
    assert m.stem < width < m.width - m.stem


def test_r_arm_parameter(ctx: DesignContext) -> None:
    n = build_n(ctx)
    short = r_from_n(n, arm=0.2)
    long = r_from_n(n, arm=0.9)
    assert bounds(short.solids[0])[2] - bounds(short.solids[0])[0] < (
        bounds(long.solids[0])[2] - bounds(long.solids[0])[0]
    )
    with pytest.raises(ValueError):
        r_from_n(n, arm=1.0)


def test_m_width_and_shared_stem(ctx: DesignContext) -> None:
    tuned = n_metrics(ctx).tuned(stem=100.0, counter=240.0)
    m_glyph = m_from_n(build_n(ctx, tuned), counter_scale=0.9)
    b = bounds(m_glyph.solids[0])
    assert b[2] - b[0] == pytest.approx(3 * 100.0 + 2 * 240.0 * 0.9)
    assert m_glyph.design is tuned
    assert m_glyph.anchor("top").x == pytest.approx((b[0] + b[2]) / 2)


def test_m_first_arch_matches_narrowed_n(ctx: DesignContext) -> None:
    n = build_n(ctx)
    rec = n_metrics(ctx)
    from typekernel.parts.weight_relief import m_counter_scale

    scale = m_counter_scale(ctx.stem)
    mm = rec.tuned(
        counter=rec.counter * scale,
        inner_crown=rec.inner_crown + 0.24 * rec.stem,
    )
    narrowed = build_n(ctx, mm)
    assert _cubics_from_left(m_from_n(n))[0] == _cubics_from_left(narrowed)[0]


def test_m_crotch_sits_on_x_height(ctx: DesignContext) -> None:
    g = build_m(ctx)
    m = n_metrics(ctx)
    ys = {round(p.y, 6) for s in g.solids[0].contours[0].segments for p in s.points}
    assert round(m.x_height, 6) in ys
    assert max(ys) == pytest.approx(m.crown_y)

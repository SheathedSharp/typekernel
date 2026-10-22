"""Continuous yokes must not leave a stem–shoulder hairline near the spring."""

from __future__ import annotations

import pytest

from typekernel.geo.joins import classify_joins
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import DesignContext, build_h, build_m, build_n, r_from_n
from typekernel.parts.primitives import double_shoulder_yoke, h_yoke, n_yoke, r_yoke


@pytest.fixture
def ctx() -> DesignContext:
    return DesignContext.geometric_sans().tuned(
        stem=88.0, x_height=548.0, sidebearing_ratio=0.09
    )


def _near_spring_hairlines(outline, spring: float, *, max_gap: float = 8.0) -> list[float]:
    """Return y samples in (spring, spring+5] where a sub-``max_gap`` slit appears."""
    bad: list[float] = []
    y = spring + 0.25
    while y <= spring + 5.0:
        iv = ink_intervals_at_y([outline], y)
        for i in range(len(iv) - 1):
            gap = iv[i + 1][0] - iv[i][1]
            if 0.0 < gap < max_gap:
                bad.append(y)
                break
        y += 0.5
    return bad


def test_n_yoke_spring_is_g1_and_sealed(ctx: DesignContext) -> None:
    ol = n_yoke(ctx, 0.0, stem_width=88.0, stem_top=ctx.x_height)
    jc = classify_joins(ol)
    assert jc.corners == 0
    assert jc.kinks == 0
    assert _near_spring_hairlines(ol, ctx.x_height) == []


def test_h_yoke_spring_has_no_cusp_hairline(ctx: DesignContext) -> None:
    ol = h_yoke(
        ctx, 0.0, stem_width=88.0, stem_top=ctx.ascender, shoulder_top=ctx.x_height
    )
    jc = classify_joins(ol)
    # Ascender stem → horizontal shoulder leave: one 90° elbow at the
    # spring is expected; cubics stay shared with ``n`` for VF.
    assert jc.corners <= 1
    assert jc.kinks == 0
    # Critical band: just above x-height spring (overshoot attachment).
    assert _near_spring_hairlines(ol, ctx.x_height, max_gap=5.0) == []


def test_m_yoke_middle_crotch_sealed(ctx: DesignContext) -> None:
    ol = double_shoulder_yoke(ctx, 0.0, stem_width=88.0, stem_top=ctx.x_height)
    assert classify_joins(ol).corners == 0
    assert _near_spring_hairlines(ol, ctx.x_height, max_gap=5.0) == []


def test_r_yoke_stem_shoulder_sealed(ctx: DesignContext) -> None:
    ol = r_yoke(ctx, 0.0, stem_width=88.0, stem_top=ctx.x_height)
    assert _near_spring_hairlines(ol, ctx.x_height, max_gap=5.0) == []


def test_builders_prefer_sealed_yokes(ctx: DesignContext) -> None:
    n = build_n(ctx)
    h = build_h(ctx)
    m = build_m(ctx)
    r = r_from_n(n, ctx)
    for g, spring in (
        (n, ctx.x_height),
        (h, ctx.x_height),
        (m, ctx.x_height),
        (r, ctx.x_height),
    ):
        assert _near_spring_hairlines(g.solids[0], spring, max_gap=5.0) == []

"""v w y x z k: compensated diagonals from the n record, fixed sealed-crotch point counts."""

from __future__ import annotations

import math

import pytest

from typekernel.axes.interpolatable import check_interpolatable
from typekernel.geo.contour import signed_area
from typekernel.geo.outline import bounds
from typekernel.optics.space import ink_intervals_at_y
from typekernel.optics.stem import diagonal_compensation
from typekernel.parts import (
    DesignContext,
    build_n,
    k_from_n,
    n_metrics,
    v_from_n,
    w_from_n,
    x_from_n,
    y_from_n,
    z_from_n,
)

DERIVE = {"v": v_from_n, "w": w_from_n, "y": y_from_n, "x": x_from_n, "z": z_from_n, "k": k_from_n}
POINTS = {"v": 8, "w": 16, "y": 9, "x": 14, "z": 10, "k": 14}


@pytest.fixture
def ctx() -> DesignContext:
    return DesignContext.code_clear()


@pytest.mark.parametrize("letter", sorted(DERIVE))
def test_single_ccw_polygon_with_fixed_point_count(ctx: DesignContext, letter: str) -> None:
    glyphs = [DERIVE[letter](build_n(ctx.tuned(stem=s))) for s in (40, 86, 160)]
    for g in glyphs:
        (contour,) = g.solids[0].contours
        assert signed_area(contour) > 0
        assert len(contour.segments) == POINTS[letter]
        assert all(s.kind == "line" for s in contour.segments)
    assert check_interpolatable([g.solids[0] for g in glyphs]) == []


def test_v_stroke_is_compensated(ctx: DesignContext) -> None:
    from typekernel.parts.diagonals import _diag_stroke_weight

    m = n_metrics(ctx)
    v = v_from_n(build_n(ctx))
    y = ctx.x_height * 0.75
    left, _ = ink_intervals_at_y(list(v.solids), y)
    hw = left[1] - left[0]
    x0, _, x1, _ = bounds(v.solids[0])
    a0 = ((x1 - x0) - 0.35 * m.stem) / 2.0
    phi = math.degrees(math.atan2(a0, ctx.x_height))
    perp = hw * math.cos(math.radians(phi))
    # v_from_n applies _diag_stroke_weight(thin=0.22); expect that stem, not raw.
    dw = _diag_stroke_weight(m.stem, thin=0.22)
    assert perp == pytest.approx(
        diagonal_compensation(phi, m.stem * dw, contrast=ctx.contrast)
    )
    assert perp < m.stem


def test_v_apex_flat_on_baseline(ctx: DesignContext) -> None:
    v = v_from_n(build_n(ctx), apex=0.5)
    (run,) = ink_intervals_at_y(list(v.solids), 0.5)
    assert run[1] - run[0] == pytest.approx(0.5 * n_metrics(ctx).stem, abs=1.0)
    assert bounds(v.solids[0])[1] == 0.0


def test_y_reaches_descender_and_w_is_wider(ctx: DesignContext) -> None:
    n = build_n(ctx)
    assert bounds(y_from_n(n).solids[0])[1] == pytest.approx(ctx.descender)
    v_w = bounds(v_from_n(n).solids[0])
    w_w = bounds(w_from_n(n).solids[0])
    # w stays clearly wider than v; exact 1.4 drifts as black optical widen runs.
    assert w_w[2] - w_w[0] > 1.3 * (v_w[2] - v_w[0])
    assert w_w[2] - w_w[0] == pytest.approx(1.4 * (v_w[2] - v_w[0]), rel=0.08)


def test_x_crosses_at_mid_height(ctx: DesignContext) -> None:
    x = x_from_n(build_n(ctx))
    assert len(ink_intervals_at_y(list(x.solids), ctx.x_height / 2.0)) == 1
    assert len(ink_intervals_at_y(list(x.solids), ctx.x_height * 0.9)) == 2


def test_z_bars_use_thin_strokes(ctx: DesignContext) -> None:
    z = z_from_n(build_n(ctx))
    x0, _, x1, _ = bounds(z.solids[0])
    (run,) = ink_intervals_at_y(list(z.solids), 4.0)
    assert run == pytest.approx((x0, x1))


def test_k_stem_reaches_ascender_and_branches(ctx: DesignContext) -> None:
    m = n_metrics(ctx).tuned(stem=100.0)
    k = k_from_n(build_n(ctx, m))
    assert bounds(k.solids[0])[3] == pytest.approx(ctx.ascender)
    stem_only = ink_intervals_at_y(list(k.solids), ctx.ascender - 10)
    assert len(stem_only) == 1 and stem_only[0][1] - stem_only[0][0] == pytest.approx(100.0)
    assert len(ink_intervals_at_y(list(k.solids), ctx.x_height * 0.8)) == 2
    assert len(ink_intervals_at_y(list(k.solids), ctx.x_height * 0.1)) == 2


def test_too_heavy_raises(ctx: DesignContext) -> None:
    n = build_n(ctx)
    with pytest.raises(ValueError, match="do not fit"):
        v_from_n(n, width=120.0)

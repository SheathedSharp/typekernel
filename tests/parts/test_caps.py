"""Capitals derive from control H and O; cap stems follow the n."""

from __future__ import annotations

import pytest

from typekernel.geo.contour import signed_area
from typekernel.geo.outline import bounds
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import (
    Controls,
    DesignContext,
    build_H,
    build_O,
    cap_o_metrics,
    h_cap_metrics,
    n_metrics,
)
from typekernel.parts.caps import CAP_STEM_RATIO


@pytest.fixture
def ctx() -> DesignContext:
    return DesignContext.code_clear()


def _box(g) -> tuple[float, float, float, float]:
    return bounds(g.solids[0])


def test_cap_stem_heavier_than_lowercase(ctx: DesignContext) -> None:
    h = h_cap_metrics(ctx)
    assert h.stem == pytest.approx(n_metrics(ctx).stem * CAP_STEM_RATIO)
    assert cap_o_metrics(ctx).thickness == pytest.approx(h.stem)
    (left, _) = ink_intervals_at_y(list(build_H(ctx).solids), ctx.cap_height * 0.25)
    assert left[1] - left[0] == pytest.approx(h.stem)


def test_h_crossbar_and_extents(ctx: DesignContext) -> None:
    h = h_cap_metrics(ctx)
    g = build_H(ctx)
    (contour,) = g.solids[0].contours
    assert signed_area(contour) > 0
    x0, y0, x1, y1 = _box(g)
    assert (x1 - x0, y0, y1) == pytest.approx((h.width, 0.0, ctx.cap_height))
    (bar,) = ink_intervals_at_y(list(g.solids), h.bar_y)
    assert bar == pytest.approx((x0, x1))
    assert h.bar_y > ctx.cap_height / 2.0


def test_o_overshoots_cap_zone(ctx: DesignContext) -> None:
    _, y0, _, y1 = _box(build_O(ctx))
    assert y0 == pytest.approx(-ctx.overshoot, abs=0.5)
    assert y1 == pytest.approx(ctx.cap_height + ctx.overshoot, abs=0.5)


def test_tuned_n_stem_reaches_caps_unless_overridden(ctx: DesignContext) -> None:
    sheet = Controls.from_context(ctx).tuned_n(stem=120.0)
    assert sheet.H.stem == pytest.approx(120.0 * CAP_STEM_RATIO)
    assert sheet.O.thickness == pytest.approx(120.0 * CAP_STEM_RATIO)
    fixed = sheet.tuned_cap_h(stem=100.0)
    assert fixed.H.stem == 100.0
    assert fixed.tuned_n(stem=60.0).H.stem == 100.0


def test_tuned_cap_h_width_moves_straight_caps(ctx: DesignContext) -> None:
    base = Controls.from_context(ctx)
    wide = base.tuned_cap_h(width=base.H.width + 80.0)
    a, b = base.build_all("HLEFT"), wide.build_all("HLEFT")
    for ch in "HLEFT":
        wa, wb = _box(a[ch])[2] - _box(a[ch])[0], _box(b[ch])[2] - _box(b[ch])[0]
        assert wb > wa, ch
    assert _box(b["H"])[2] - _box(b["H"])[0] == pytest.approx(base.H.width + 80.0)


@pytest.mark.parametrize(
    ("ch", "runs_mid", "runs_top"),
    [("I", 1, 1), ("L", 1, 1), ("E", 1, 1), ("F", 1, 1), ("T", 1, 1)],
)
def test_straight_caps_shapes(ctx: DesignContext, ch: str, runs_mid: int, runs_top: int) -> None:
    g = Controls.from_context(ctx).build(ch)
    (contour,) = g.solids[0].contours
    assert signed_area(contour) > 0
    assert len(ink_intervals_at_y(list(g.solids), ctx.cap_height * 0.3)) == runs_mid
    assert len(ink_intervals_at_y(list(g.solids), ctx.cap_height - 2.0)) == runs_top


def test_e_arm_lengths(ctx: DesignContext) -> None:
    g = Controls.from_context(ctx).build("E")
    h = h_cap_metrics(ctx)
    (top,) = ink_intervals_at_y(list(g.solids), ctx.cap_height - 2.0)
    (mid,) = ink_intervals_at_y(list(g.solids), h.bar_y)
    (foot,) = ink_intervals_at_y(list(g.solids), 2.0)
    assert mid[1] < top[1] < foot[1]

"""f t j hook from the r arm; crossbars are part of one fixed contour."""

from __future__ import annotations

import pytest

from typekernel.font import Font, Master, check_masters
from typekernel.geo.contour import signed_area
from typekernel.geo.outline import bounds
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import (
    Controls,
    DesignContext,
    build_n,
    f_from_n,
    j_from_n,
    n_metrics,
    t_from_n,
)
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.control import _hook_shoulder_rise


@pytest.fixture
def ctx() -> DesignContext:
    return DesignContext.code_clear()


def test_f_hook_at_ascender_and_bar_at_x_height(ctx: DesignContext) -> None:
    m = n_metrics(ctx)
    f = f_from_n(build_n(ctx))
    (contour,) = f.solids[0].contours
    assert signed_area(contour) > 0
    _, y0, _, y1 = bounds(f.solids[0])
    rise = _hook_shoulder_rise(ctx, m)
    assert y0 == 0.0 and y1 == pytest.approx(ctx.ascender + rise)
    assert rise > ctx.overshoot
    tb = m.stem * ctx.contrast * 0.95
    (bar,) = ink_intervals_at_y(list(f.solids), ctx.x_height - tb / 2.0)
    (stem,) = ink_intervals_at_y(list(f.solids), ctx.x_height / 2.0)
    assert stem[1] - stem[0] == pytest.approx(m.stem)
    assert bar[1] - bar[0] == pytest.approx(m.stem + 0.94 * m.counter)


def test_t_hook_on_baseline(ctx: DesignContext) -> None:
    m = n_metrics(ctx)
    t = t_from_n(build_n(ctx))
    (contour,) = t.solids[0].contours
    assert signed_area(contour) > 0
    rise = _hook_shoulder_rise(ctx, m)
    _, y0, _, y1 = bounds(t.solids[0])
    assert y0 == pytest.approx(-rise)
    assert y1 == pytest.approx(ctx.x_height + 0.3 * (ctx.ascender - ctx.x_height))
    # the stem bends right at the bottom: ink right of the stem near the baseline
    runs = ink_intervals_at_y(list(t.solids), 4.0)
    stem_left = bounds(t.solids[0])[0] + 0.42 * m.counter
    assert max(r[1] for r in runs) > stem_left + 2 * m.stem


def test_j_hook_in_descender_with_tittle(ctx: DesignContext) -> None:
    m = n_metrics(ctx)
    j = j_from_n(build_n(ctx))
    body, dot = j.solids
    rise = _hook_shoulder_rise(ctx, m)
    assert bounds(body)[1] == pytest.approx(ctx.descender - rise)
    assert bounds(body)[3] == pytest.approx(ctx.x_height)
    assert bounds(dot)[1] > ctx.x_height
    # hook curls left of the stem
    (stem,) = ink_intervals_at_y([body], ctx.x_height / 2.0)
    low = ink_intervals_at_y([body], ctx.descender + 4.0)
    assert min(r[0] for r in low) < stem[0] - m.stem


def test_n_shoulder_unchanged_by_hook_tuning(ctx: DesignContext) -> None:
    n = build_n(ctx)
    assert bounds(n.solids[0])[3] == pytest.approx(ctx.x_height + ctx.overshoot)


def test_j_hook_outer_segment_count_fixed_across_stems() -> None:
    ctx = DesignContext.humanist_sans()
    ref = j_from_n(build_n(ctx), ctx)
    body = ComposedGlyph((ref.solids[0],), (), ref.advance, ctx)
    ref_n = len(body.solids[0].contours[0].segments)
    for stem in (30.0, 86.0, 220.0):
        heavy = ctx.tuned(stem=stem)
        j = j_from_n(build_n(heavy), heavy)
        body = ComposedGlyph((j.solids[0],), (), j.advance, heavy)
        assert len(body.solids[0].contours[0].segments) == ref_n


def test_j_body_interpolates_across_weight_ladder() -> None:
    ctx = DesignContext.humanist_sans()
    charset = "j"
    light = Controls.from_context(ctx.tuned(stem=30.0))
    bold = Controls.from_context(ctx.tuned(stem=220.0))
    reg_font = Font.from_context(ctx, "J Sans", "Regular", weight_class=400)
    bold_font = Font.from_context(ctx, "J Sans", "Bold", weight_class=700)
    reg_font.add_chars(
        {
            ch: ComposedGlyph((g.solids[0],), (), g.advance, ctx)
            for ch, g in light.build_all(charset).items()
        }
    )
    bold_font.add_chars(
        {
            ch: ComposedGlyph((g.solids[0],), (), g.advance, ctx)
            for ch, g in bold.build_all(charset).items()
        }
    )
    masters = [Master({"wght": 400.0}, reg_font), Master({"wght": 700.0}, bold_font)]
    assert check_masters(masters) == []


def test_heavy_f_drops_bar_below_crotch(ctx: DesignContext) -> None:
    heavy = DesignContext.mono().tuned(stem=170.0)
    f = f_from_n(build_n(heavy))
    assert len(f.solids[0].contours[0].segments) == len(
        f_from_n(build_n(DesignContext.mono())).solids[0].contours[0].segments
    )

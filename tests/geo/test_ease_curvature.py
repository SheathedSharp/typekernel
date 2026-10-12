"""Curvature easing: straight↔round G2 harmonize on synthetic fixtures."""

from __future__ import annotations

import pytest

from typekernel.geo.joins import (
    classify_joins,
    curvature_jump,
    ease_curvature,
    straight_curve_jump,
)
from typekernel.geo.path_builder import PathBuilder
from typekernel.parts import DesignContext, GlyphAssembler, vertical_stem
from typekernel.parts.primitives import bowl, u_bowl


def _stadium(length: float = 80.0, radius: float = 100.0, thick: float = 40.0):
    """Racetrack ring: straight flanks + semicircle caps (classic straight→round)."""
    b = PathBuilder()
    L, R = length, radius
    b.moveTo(-L, -R)
    b.lineTo(L, -R)
    b.arcTo(L, 0, R, R, 90, start_angle_deg=-90)
    b.lineTo(-L, R)
    b.arcTo(-L, 0, R, R, -90, start_angle_deg=90)
    b.closePath()
    ri = R - thick
    b.moveTo(-L, -ri)
    b.arcTo(-L, 0, ri, ri, 90, start_angle_deg=-90)
    b.lineTo(L, ri)
    b.arcTo(L, 0, ri, ri, -90, start_angle_deg=90)
    b.lineTo(-L, -ri)
    b.closePath()
    return b.build()


def _rect_into_arc():
    """Vertical stem line into a quarter-circle, closed as a thick J-hook fragment."""
    # Outer path: down the right stem, quarter out, left, up inner, quarter back.
    t, r = 40.0, 80.0
    b = PathBuilder()
    b.moveTo(t, 200.0)
    b.lineTo(t, r)  # stem right edge down to arc start
    b.arcTo(0.0, r, r, r, -90.0, start_angle_deg=0.0)  # to (-r? center 0,r start at (r,r)=(t,r) if t==r
    # Redo with consistent geometry: stem at x=r
    b = PathBuilder()
    b.moveTo(r, 220.0)
    b.lineTo(r, r)
    b.arcTo(0.0, r, r, r, -90.0, start_angle_deg=0.0)  # ends at (0, 0)
    b.lineTo(0.0, t)
    b.lineTo(r - t, t)
    b.lineTo(r - t, r)
    # inner arc back
    ri = r - t
    b.arcTo(0.0, r, ri, ri, 0.0, start_angle_deg=-90.0)
    b.lineTo(r - t, 220.0)
    b.closePath()
    return b.build()


def test_stadium_straight_curve_jump_drops_to_near_zero() -> None:
    raw = _stadium()
    before = straight_curve_jump(raw)
    assert before > 0.5  # untreated line/arc join jumps hard
    eased = ease_curvature(raw)
    after = straight_curve_jump(eased)
    assert after < 0.05
    # Classifier regression: easing must not invent kinks
    assert classify_joins(eased).kinks == 0


def test_stadium_overall_curvature_jump_improves() -> None:
    raw = _stadium()
    eased = ease_curvature(raw)
    assert curvature_jump(eased) <= curvature_jump(raw)
    assert curvature_jump(eased) < 0.05 or straight_curve_jump(eased) < 0.05


def test_rect_into_arc_no_new_kinks() -> None:
    """Stem+hook fragment: easing must not invent kinks (jump may be unchanged
    when the only line/arc joins are both-G1 fillets, which are skipped)."""
    raw = _rect_into_arc()
    assert classify_joins(raw).kinks == 0
    before = straight_curve_jump(raw)
    eased = ease_curvature(raw, insert_length=20.0)
    after = straight_curve_jump(eased)
    assert classify_joins(eased).kinks == 0
    assert after <= before + 1e-9


def test_one_sided_g1_arc_insert_reduces_jump() -> None:
    """Line → quarter-circle → line with G1 only at the start (far end bent)."""
    b = PathBuilder()
    # Vertical stem into quarter-circle that meets the next line at 90° (not G1).
    b.moveTo(100, 300)
    b.lineTo(100, 100)
    b.arcTo(0, 100, 100, 100, -90, start_angle_deg=0)  # ends at (0, 0)
    b.lineTo(0, 40)  # continuing down — NOT tangent to arc end
    b.lineTo(60, 40)
    b.lineTo(60, 100)
    b.lineTo(60, 300)
    b.closePath()
    raw = b.build()
    before = straight_curve_jump(raw)
    assert before > 0.5
    eased = ease_curvature(raw, insert_length=24.0)
    after = straight_curve_jump(eased)
    assert classify_joins(eased).kinks == 0
    assert after < 0.05


def test_ease_is_noop_on_polyline_rectangle() -> None:
    b = PathBuilder()
    b.moveTo(0, 0)
    b.lineTo(100, 0)
    b.lineTo(100, 80)
    b.lineTo(0, 80)
    b.closePath()
    rect = b.build()
    eased = ease_curvature(rect)
    assert classify_joins(eased).terminals == classify_joins(rect).terminals
    assert straight_curve_jump(eased) == 0.0


def test_assembler_ease_curvature_pass_on_u_bowl() -> None:
    ctx = DesignContext.geometric_sans()
    trough = u_bowl(ctx, 0.0, ctx.stem * 2 + ctx.x_height * 0.5, ctx.x_height, -ctx.overshoot)
    plain = GlyphAssembler(ctx).add(trough).build()
    eased = GlyphAssembler(ctx).add(trough).ease_curvature().build()
    # Both valid glyphs; eased should not increase straight-curve jump
    from typekernel.geo.joins import straight_curve_jump as scj

    assert scj(eased.solids[0]) <= scj(plain.solids[0]) + 1e-9
    assert scj(eased.solids[0]) < 0.05


def test_assembler_ease_after_bowl_difference() -> None:
    ctx = DesignContext.geometric_sans()
    ry = ctx.x_height / 2 + ctx.overshoot
    outer, hole = bowl(ctx, ry, ctx.x_height / 2, rx=ry, ry=ry)
    stem = vertical_stem(ctx, ry * 2 - ctx.stem, 0.0, ctx.x_height)
    g = (
        GlyphAssembler(ctx)
        .add(outer)
        .add(stem)
        .union_solids()
        .add_hole(hole)
        .subtract_holes()
        .ease_curvature()
        .build()
    )
    assert g.advance > 0
    assert classify_joins(g.solids[0]).kinks == 0



def _g1_g1_quarter():
    """Horizontal line → kappa quarter → vertical line (both joins G1)."""
    b = PathBuilder()
    b.moveTo(0.0, 100.0)
    b.lineTo(100.0, 100.0)
    b.arcTo(100.0, 0.0, 100.0, 100.0, 0.0, start_angle_deg=90.0)
    b.lineTo(200.0, -80.0)
    b.lineTo(260.0, -80.0)
    b.lineTo(260.0, 160.0)
    b.lineTo(0.0, 160.0)
    b.closePath()
    return b.build()


def test_both_end_clothoid_eases_g1_g1_quarter() -> None:
    raw = _g1_g1_quarter()
    before = straight_curve_jump(raw)
    assert before > 0.5
    assert len(raw.contours[0].segments) == 7
    eased = ease_curvature(raw, insert_length=28.0, both_ends=True)
    after = straight_curve_jump(eased)
    assert after < 0.05
    assert classify_joins(eased).kinks == 0
    # Two transition cubics inserted → segment count grows
    assert len(eased.contours[0].segments) > len(raw.contours[0].segments)


def test_both_ends_false_leaves_g1_g1_quarter() -> None:
    raw = _g1_g1_quarter()
    before = straight_curve_jump(raw)
    left = ease_curvature(raw, insert_length=28.0, both_ends=False)
    assert straight_curve_jump(left) == pytest.approx(before)
    assert len(left.contours[0].segments) == len(raw.contours[0].segments)

"""Parameterised continuous-curve skeleton letter recipes."""

from __future__ import annotations

import importlib.util

import pytest

from typekernel.geo.outline import bounds
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.optics.stem import measure_vertical_stem
from typekernel.parts import (
    DesignContext,
    build_skel_letter,
    build_skel_word,
    skel_i,
    skel_l,
    skel_n,
    skel_o,
    skeleton_n,
)
from typekernel.parts.skeleton_recipes import SKEL_BUILDERS

HAS_PATHOPS = importlib.util.find_spec("pathops") is not None

pytestmark = pytest.mark.skipif(not HAS_PATHOPS, reason="pathops for union")


def test_builders_cover_ohio_letters() -> None:
    assert set("ohio").issubset(SKEL_BUILDERS)


def test_n_scales_with_aperture() -> None:
    narrow = DesignContext.geometric_sans().tuned(aperture=0.2)
    wide = DesignContext.geometric_sans().tuned(aperture=0.9)
    sn = skeleton_n(narrow)
    sw = skeleton_n(wide)
    right_n = next(s for s in sn.strokes if s.name == "right")
    right_w = next(s for s in sw.strokes if s.name == "right")
    assert right_w.points[0][0] > right_n.points[0][0]


def test_o_overshoot_extends_below_baseline() -> None:
    ctx = DesignContext.paper_ink()
    g = skel_o(ctx)
    bb = bounds(g.solids[0])
    assert bb[1] < -ctx.overshoot * 0.4


def test_o_and_n_use_cubics_not_bead_polylines() -> None:
    """Arches/bowls must be continuous cubics — not dense line chains."""
    ctx = DesignContext.code_clear()
    o = skel_o(ctx).solids[0]
    n = skel_n(ctx).solids[0]
    o_cub = sum(1 for c in o.contours for s in c.segments if isinstance(s, CubicSegment))
    n_cub = sum(1 for c in n.contours for s in c.segments if isinstance(s, CubicSegment))
    o_line = sum(1 for c in o.contours for s in c.segments if isinstance(s, LineSegment))
    assert o_cub >= 4
    assert n_cub >= 2
    # Superellipse o is cubic-only; n has stems (lines) + arch cubics
    assert o_cub > o_line


def test_i_has_stem_and_tittle() -> None:
    ctx = DesignContext.code_clear()
    g = skel_i(ctx)
    assert len(g.solids) >= 1
    # Combined ink spans baseline through tittle
    from typekernel.geo.layout import union_bounds

    bb = union_bounds(list(g.solids))
    assert bb[1] <= 1.0
    assert bb[3] > ctx.x_height + ctx.stem * 0.4


def test_stem_width_tracks_context() -> None:
    ctx = DesignContext.geometric_sans().tuned(stem=80.0, contrast=1.0)
    g = skel_l(ctx)
    bb = bounds(g.solids[0])
    w = measure_vertical_stem(g.solids[0], 0.5 * (bb[0] + bb[2]))
    assert w == pytest.approx(80.0, abs=2.0)


def test_build_skel_word_ohio() -> None:
    ctx = DesignContext.code_clear()
    glyphs = build_skel_word("ohio", ctx)
    assert len(glyphs) == 4
    assert all(g.advance > 0 for g in glyphs)


def test_c_shallow_shear_not_deep() -> None:
    from typekernel.parts.skeleton_recipes import _shallow_shear_deg

    ctx = DesignContext.open_print()
    assert _shallow_shear_deg(ctx) <= 10.0


def test_unknown_letter_raises() -> None:
    with pytest.raises(KeyError, match="no skeleton recipe"):
        build_skel_letter("z", DesignContext.geometric_sans())

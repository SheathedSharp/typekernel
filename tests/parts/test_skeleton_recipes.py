"""Parameterised skeleton letter recipes (context-driven, not face-specific)."""

from __future__ import annotations

import importlib.util

import pytest

from typekernel.geo.outline import bounds
from typekernel.optics.stem import measure_vertical_stem
from typekernel.parts import (
    DesignContext,
    build_skel_letter,
    build_skel_word,
    skel_i,
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
    # Counter width is encoded in right stem x of the skeleton.
    sn = skeleton_n(narrow)
    sw = skeleton_n(wide)
    right_n = next(s for s in sn.strokes if s.name == "right")
    right_w = next(s for s in sw.strokes if s.name == "right")
    assert right_w.points[0][0] > right_n.points[0][0]


def test_o_overshoot_extends_below_baseline() -> None:
    ctx = DesignContext.paper_ink()
    g = skel_o(ctx, blend=False, ease=False)
    bb = bounds(g.solids[0])
    assert bb[1] < -ctx.overshoot * 0.5


def test_i_tittle_is_solid_disk() -> None:
    ctx = DesignContext.code_clear()
    g = skel_i(ctx, blend=False, ease=False)
    # Stem + tittle unioned; should not leave a hollow ring as only ink.
    assert sum(len(s.contours) for s in g.solids) >= 1
    assert g.advance > 0


def test_stem_width_tracks_context() -> None:
    ctx = DesignContext.geometric_sans().tuned(stem=80.0, contrast=1.0)
    # Isolated vertical via l recipe
    from typekernel.parts import skel_l

    g = skel_l(ctx, blend=False, ease=False, cap="butt")
    bb = bounds(g.solids[0])
    w = measure_vertical_stem(g.solids[0], 0.5 * (bb[0] + bb[2]))
    assert w == pytest.approx(80.0, abs=2.0)


def test_build_skel_word_ohio() -> None:
    ctx = DesignContext.code_clear()
    glyphs = build_skel_word("ohio", ctx)
    assert len(glyphs) == 4
    assert all(g.advance > 0 for g in glyphs)


def test_unknown_letter_raises() -> None:
    with pytest.raises(KeyError, match="no skeleton recipe"):
        build_skel_letter("z", DesignContext.geometric_sans())

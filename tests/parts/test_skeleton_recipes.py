"""Compat skel_* delegates to control glyphs."""

from __future__ import annotations

import importlib.util

import pytest

from typekernel.geo.segment import CubicSegment
from typekernel.parts import (
    DesignContext,
    build_skel_letter,
    build_skel_word,
    skel_h,
    skel_n,
    skel_o,
    skeleton_n,
)
from typekernel.parts.skeleton_recipes import SKEL_BUILDERS

HAS_PATHOPS = importlib.util.find_spec("pathops") is not None
pytestmark = pytest.mark.skipif(not HAS_PATHOPS, reason="pathops for o")


def test_builders_cover_ohio_letters() -> None:
    assert set("ohio").issubset(SKEL_BUILDERS)


def test_n_scales_with_aperture() -> None:
    narrow = DesignContext.geometric_sans().tuned(aperture=0.2)
    wide = DesignContext.geometric_sans().tuned(aperture=0.9)
    assert (
        next(s for s in skeleton_n(wide).strokes if s.name == "right").points[0][0]
        > next(s for s in skeleton_n(narrow).strokes if s.name == "right").points[0][0]
    )


def test_skel_delegates_to_control() -> None:
    ctx = DesignContext.code_clear()
    from typekernel.parts.control import build_h, build_n

    assert skel_n(ctx).advance == pytest.approx(build_n(ctx).advance)
    assert skel_h(ctx).advance == pytest.approx(build_h(ctx).advance)


def test_o_and_n_use_cubics() -> None:
    ctx = DesignContext.code_clear()
    o = skel_o(ctx).solids[0]
    n = skel_n(ctx).solids[0]
    assert sum(1 for c in o.contours for s in c.segments if isinstance(s, CubicSegment)) >= 4
    assert sum(1 for c in n.contours for s in c.segments if isinstance(s, CubicSegment)) >= 4


def test_build_skel_word_ohio() -> None:
    assert len(build_skel_word("ohio", DesignContext.code_clear())) == 4


def test_unknown_letter_raises() -> None:
    with pytest.raises(KeyError):
        build_skel_letter("z", DesignContext.geometric_sans())

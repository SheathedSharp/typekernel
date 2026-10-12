"""Stable outline hash regression checks."""

from __future__ import annotations

from pathlib import Path

from typekernel.geo.contour import Contour
from typekernel.geo.fixtures import load_synthetic_outline
from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment
from typekernel.qa.outline_hash import outline_hash

FIXTURE = Path(__file__).parent.parent / "fixtures" / "synthetic_O.json"


def test_same_outline_same_hash() -> None:
    a = load_synthetic_outline(FIXTURE)
    b = load_synthetic_outline(FIXTURE)
    assert outline_hash(a) == outline_hash(b)
    assert len(outline_hash(a)) == 64  # sha256 hex


def test_tweaked_point_changes_hash() -> None:
    outline = load_synthetic_outline(FIXTURE)
    base = outline_hash(outline)
    first = outline.contours[0]
    seg0 = first.segments[0]
    assert isinstance(seg0, CubicSegment)
    tweaked_seg = CubicSegment(
        Point(seg0.p0.x + 1.0, seg0.p0.y),
        seg0.p1,
        seg0.p2,
        seg0.p3,
    )
    tweaked_contour = Contour((tweaked_seg,) + first.segments[1:], closed=first.closed)
    tweaked = Outline((tweaked_contour,) + outline.contours[1:])
    assert outline_hash(tweaked) != base


def test_square_hash_is_deterministic() -> None:
    builder = PathBuilder()
    builder.moveTo(0, 0)
    builder.lineTo(100, 0)
    builder.lineTo(100, 100)
    builder.lineTo(0, 100)
    builder.closePath()
    outline = builder.build()
    assert outline_hash(outline) == outline_hash(outline)


def test_empty_outline_hashes() -> None:
    digest = outline_hash(Outline(()))
    assert len(digest) == 64

"""Bowl shape=superellipse synthetic fixtures."""

from __future__ import annotations

import pytest

from typekernel.geo.outline import bounds
from typekernel.parts import DesignContext, bowl, superellipse_ring


def test_bowl_ellipse_default_unchanged() -> None:
    ctx = DesignContext.geometric_sans()
    outer, inner = bowl(ctx, 100.0, 100.0)
    assert outer.contour_count == 1
    assert inner.contour_count == 1


def test_bowl_superellipse_ring() -> None:
    ctx = DesignContext.geometric_sans()
    outer, inner = bowl(ctx, 200.0, 200.0, rx=120.0, ry=100.0, shape="superellipse", n=2.8)
    oo = bounds(outer)
    ii = bounds(inner)
    assert oo[2] - oo[0] > ii[2] - ii[0]
    assert outer.contours[0].closed


def test_superellipse_ring_helper() -> None:
    ctx = DesignContext.geometric_sans()
    outer, _inner = superellipse_ring(ctx, 0.0, 0.0, rx=90.0, ry=70.0, n=3.0, tension=1.1)
    assert bounds(outer)[2] == pytest.approx(90.0, abs=0.05)


def test_bowl_rejects_unknown_shape() -> None:
    ctx = DesignContext.geometric_sans()
    with pytest.raises(ValueError, match="shape"):
        bowl(ctx, 0.0, 0.0, shape="squircloid")

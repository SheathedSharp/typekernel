"""Shared script stroke primitives (chaikin / shear / rails)."""

from __future__ import annotations

from typekernel.parts.script import (
    chaikin_subdivide,
    entry_rail,
    exit_rail,
    shear_xy,
    slant_shear,
)


def test_chaikin_preserves_endpoints() -> None:
    pts = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)]
    out = chaikin_subdivide(pts, rounds=3)
    assert out[0] == pts[0]
    assert out[-1] == pts[-1]
    assert len(out) > len(pts)


def test_shear_xy_and_slant_shear() -> None:
    assert slant_shear(0.0) == 0.0
    assert shear_xy(10.0, 20.0, 0.5) == (20.0, 20.0)


def test_entry_exit_rail_shapes() -> None:
    e = entry_rail(0.0, 100.0, y=50.0, lift=80.0)
    assert len(e) == 3
    assert e[0][0] == 0.0 and e[-1] == (100.0, 80.0)
    x = exit_rail(0.0, 100.0, y=50.0, lift=80.0)
    assert len(x) == 3
    assert x[-1][0] == 100.0

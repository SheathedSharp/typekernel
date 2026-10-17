"""Shared script stroke primitives (chaikin / shear / rails)."""

from __future__ import annotations

from typekernel.parts.script import (
    bridge_script_rails,
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


def test_nib_polyline_and_ellipse() -> None:
    from typekernel.parts.script import (
        NibSpec,
        nib_ellipse_stroke,
        nib_polyline_stroke,
        slant_shear,
    )

    nib = NibSpec(36.0, 0.48, 38.0)
    shear = slant_shear(28.0)
    poly = nib_polyline_stroke(
        "stem", [(0.0, 0.0), (10.0, 40.0), (30.0, 20.0)], nib, shear=shear
    )
    assert poly.thickness == 36.0
    assert len(poly.points) > 3
    ring = nib_ellipse_stroke("ring", 100.0, 200.0, 40.0, 80.0, nib, shear=shear)
    assert ring.closed
    assert ring.beziers is not None and len(ring.beziers) == 4


def test_trace_nib_strokes_builds_glyph() -> None:
    from typekernel.parts import DesignContext
    from typekernel.parts.script import (
        NibSpec,
        nib_ellipse_stroke,
        slant_shear,
        trace_nib_strokes,
    )

    nib = NibSpec(36.0, 0.48, 38.0)
    ring = nib_ellipse_stroke(
        "ring", 175.0, 210.0, 100.0, 200.0, nib, shear=slant_shear(28.0)
    )
    ctx = DesignContext.display().tuned(stem=36.0, contrast=0.48)
    glyph = trace_nib_strokes([ring], ctx, min_contour_area=350.0)
    assert glyph.solids


def test_polish_script_joins_is_explicit() -> None:
    from typekernel.parts import DesignContext
    from typekernel.parts.script import (
        NibSpec,
        nib_ellipse_stroke,
        polish_script_joins,
        slant_shear,
        trace_nib_strokes,
    )

    nib = NibSpec(36.0, 0.48, 38.0)
    ring = nib_ellipse_stroke(
        "ring", 175.0, 210.0, 100.0, 200.0, nib, shear=slant_shear(28.0)
    )
    ctx = DesignContext.display().tuned(stem=36.0, contrast=0.48)
    raw = trace_nib_strokes([ring], ctx, polish_joins=False)
    polished = polish_script_joins(raw)
    assert polished.solids
    # Default trace path applies polish.
    default = trace_nib_strokes([ring], ctx, polish_joins=True)
    assert default.solids


def test_bridge_script_rails_joins_exit_to_entry() -> None:
    ex = exit_rail(0.0, 80.0, y=40.0, lift=60.0)
    en = entry_rail(100.0, 180.0, y=40.0, lift=70.0)
    bridged = bridge_script_rails(ex, en, mid_dip=5.0)
    assert bridged[0] == ex[0]
    assert bridged[-1] == en[-1]
    assert len(bridged) == len(ex) + 1 + len(en)
    mid = bridged[len(ex)]
    assert mid[1] < (ex[-1][1] + en[0][1]) * 0.5

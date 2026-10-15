"""TK-402: oblique pre-split parameters (library; VF wiring deferred)."""

from __future__ import annotations

import math

from typekernel.axes.slant import ObliqueTransform
from typekernel.geo.extrema import (
    cubic_has_off_node_axis_extrema,
    oblique_compat_split_ts,
    outline_oblique_compat_splits,
)
from typekernel.geo.segment import CubicSegment
from typekernel.parts import Controls, DesignContext


def test_oblique_pre_split_then_shear_clears_r4_on_o() -> None:
    reg = Controls.from_context(DesignContext.code_clear())
    o = reg.build("o")
    shear = math.tan(math.radians(10.0))
    transform = ObliqueTransform(10.0)

    def slant_with_compat(solid):
        split = outline_oblique_compat_splits(solid, shear)
        return transform.apply(split)

    slanted = slant_with_compat(o.solids[0])
    for seg in slanted.iter_segments():
        if isinstance(seg, CubicSegment):
            assert not cubic_has_off_node_axis_extrema(seg)


def test_oblique_compat_split_ts_nonempty_on_ellipse_quarter() -> None:
    reg = Controls.from_context(DesignContext.code_clear())
    o = reg.build("o")
    seg = next(o.solids[0].iter_segments())
    assert isinstance(seg, CubicSegment)
    shear = math.tan(math.radians(10.0))
    assert oblique_compat_split_ts(seg, shear)

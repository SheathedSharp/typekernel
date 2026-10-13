"""Axis masters and designed deltas for typekernel.

Weight and other axis variation are expressed as **point/handle deltas** or
master pairs (see :class:`~typekernel.axes.weight_delta.WeightDelta`), then
written to a ``.designspace`` through fontTools.designspaceLib.

This package is **not** stroke expansion: there is no public buffer-weight or
pen-radius API here, and there never should be.
"""

from __future__ import annotations

from typekernel.axes.designspace_export import write_weight_designspace
from typekernel.axes.interpolatable import check_interpolatable
from typekernel.axes.masters import GlyphMasters
from typekernel.axes.slant import ObliqueTransform
from typekernel.axes.weight_delta import WeightDelta

__all__ = [
    "GlyphMasters",
    "ObliqueTransform",
    "WeightDelta",
    "check_interpolatable",
    "write_weight_designspace",
]

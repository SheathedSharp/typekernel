"""Axis masters and designed deltas for typekernel.

Weight and other axis variation are expressed as **point/handle deltas** or
master pairs (see :class:`~typekernel.axes.weight_delta.WeightDelta`), then
written to a ``.designspace`` through fontTools.designspaceLib.

This package is **not** stroke expansion: there is no public buffer-weight or
pen-radius API here, and there never should be.
"""

from __future__ import annotations

from typekernel.axes.designspace_export import write_weight_designspace
from typekernel.axes.family import (
    FamilyMember,
    FamilySpec,
    link_family,
    read_family_identity,
)
from typekernel.axes.instantiate import instance_static, instance_statics
from typekernel.axes.interpolatable import (
    check_drawing_interpolatable,
    check_interpolatable,
)
from typekernel.axes.masters import GlyphMasters
from typekernel.axes.slant import ObliqueTransform
from typekernel.axes.spec import Axis, Instance, MasterSpec
from typekernel.axes.weight_delta import WeightDelta

__all__ = [
    "Axis",
    "FamilyMember",
    "FamilySpec",
    "GlyphMasters",
    "Instance",
    "MasterSpec",
    "ObliqueTransform",
    "WeightDelta",
    "check_drawing_interpolatable",
    "check_interpolatable",
    "instance_static",
    "instance_statics",
    "link_family",
    "read_family_identity",
    "write_weight_designspace",
]

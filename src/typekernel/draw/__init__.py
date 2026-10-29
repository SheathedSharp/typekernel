"""draw — Fragment / Writer / Drawing kernel (ARCHITECTURE.md「交接规格」)."""

from __future__ import annotations

from typekernel.draw.construct import (
    diagonal_band,
    hook,
    spring,
    superellipse_quarter,
    tensioned_arc,
)
from typekernel.draw.drawing import ContourRole, Drawing, Measure, Slot
from typekernel.draw.errors import ContinuityError
from typekernel.draw.fragment import Fragment, Node
from typekernel.draw.slots import (
    CornerFill,
    CornerFiller,
    CornerSite,
    EndFill,
    EndFiller,
    EndSite,
    SlotFillError,
    apply_slots,
)
from typekernel.draw.writer import Writer

__all__ = [
    "ContinuityError",
    "ContourRole",
    "CornerFill",
    "CornerFiller",
    "CornerSite",
    "Drawing",
    "EndFill",
    "EndFiller",
    "EndSite",
    "Fragment",
    "Measure",
    "Node",
    "Slot",
    "SlotFillError",
    "Writer",
    "apply_slots",
    "diagonal_band",
    "hook",
    "spring",
    "superellipse_quarter",
    "tensioned_arc",
]

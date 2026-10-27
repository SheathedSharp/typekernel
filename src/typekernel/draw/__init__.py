"""draw — Fragment / Writer / Drawing kernel (ARCHITECTURE.md §9)."""

from __future__ import annotations

from typekernel.draw.drawing import ContourRole, Drawing, Slot
from typekernel.draw.errors import ContinuityError
from typekernel.draw.fragment import Fragment, Node
from typekernel.draw.writer import Writer

__all__ = [
    "ContinuityError",
    "ContourRole",
    "Drawing",
    "Fragment",
    "Node",
    "Slot",
    "Writer",
]

"""Corner fillers (ARCHITECTURE.md §9.5 / §9.10)."""

from __future__ import annotations

from typekernel.plugins.corners.bracketed import bracketed
from typekernel.plugins.corners.plain import plain
from typekernel.plugins.corners.rounded import rounded
from typekernel.plugins.corners.slab import slab
from typekernel.plugins.corners.wedge import wedge

__all__ = ["bracketed", "plain", "rounded", "slab", "wedge"]

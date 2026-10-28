"""Corner fillers (ARCHITECTURE.md 槽位与填充协议 / 落地顺序)."""

from __future__ import annotations

from typekernel.plugins.corners.bracketed import bracketed
from typekernel.plugins.corners.ink_trap import ink_trap
from typekernel.plugins.corners.plain import plain
from typekernel.plugins.corners.rounded import rounded
from typekernel.plugins.corners.slab import slab
from typekernel.plugins.corners.wedge import wedge

__all__ = ["bracketed", "ink_trap", "plain", "rounded", "slab", "wedge"]

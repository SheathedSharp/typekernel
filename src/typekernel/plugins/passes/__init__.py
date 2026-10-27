"""Optical pass plugins (ARCHITECTURE.md §9.10 M3)."""

from __future__ import annotations

from typekernel.plugins.passes.diagonal_comp import compensated_weight, diagonal_comp
from typekernel.plugins.passes.overshoot import overshoot

__all__ = ["compensated_weight", "diagonal_comp", "overshoot"]

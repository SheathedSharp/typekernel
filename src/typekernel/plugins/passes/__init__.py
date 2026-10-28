"""Optical pass plugins (ARCHITECTURE.md「落地顺序」)."""

from __future__ import annotations

from typekernel.plugins.passes.crotch_thin import crotch_thin
from typekernel.plugins.passes.diagonal_comp import compensated_weight, diagonal_comp
from typekernel.plugins.passes.overshoot import overshoot

__all__ = ["compensated_weight", "crotch_thin", "diagonal_comp", "overshoot"]

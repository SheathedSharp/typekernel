"""Pair and class kerning tables (从 parts 迁出)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

__all__ = ["ClassKernPair", "ClassKernTable", "KernClass", "KernPair", "KernTable"]

Side = Literal["left", "right", "both"]


@dataclass(frozen=True, slots=True)
class KernPair:
    """One pairwise kerning adjustment in design units."""

    left: str
    right: str
    value: float


@dataclass(frozen=True, slots=True)
class KernTable:
    """Minimal kerning dictionary keyed by ``(left, right)``."""

    pairs: tuple[KernPair, ...] = ()

    def lookup(self, left: str, right: str) -> float:
        for p in self.pairs:
            if p.left == left and p.right == right:
                return p.value
        return 0.0

    def with_pair(self, left: str, right: str, value: float) -> KernTable:
        kept = [p for p in self.pairs if not (p.left == left and p.right == right)]
        kept.append(KernPair(left, right, value))
        return KernTable(tuple(kept))


@dataclass(frozen=True, slots=True)
class KernClass:
    """Named glyph class for class-based kerning."""

    name: str
    members: tuple[str, ...]
    side: Side = "both"


@dataclass(frozen=True, slots=True)
class ClassKernPair:
    """Kern value between two :class:`KernClass` names."""

    left_class: str
    right_class: str
    value: float


@dataclass(frozen=True, slots=True)
class ClassKernTable:
    """Class kerning: glyph classes plus class-pair values."""

    classes: tuple[KernClass, ...] = ()
    pairs: tuple[ClassKernPair, ...] = ()

"""Metrics keys engine (target-architecture §5.3).

P1-2 ships the declarative types so :class:`~typekernel.project.Project` can
reference them. Resolve / pack land in P1-4.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal

from typekernel.font.kerning import ClassKernPair, KernClass, KernPair

__all__ = [
    "Abs",
    "Kerning",
    "Metrics",
    "Mirror",
    "Optical",
    "Ref",
    "Side",
    "Stem",
    "Token",
]


@dataclass(frozen=True, slots=True)
class Abs:
    value: float


@dataclass(frozen=True, slots=True)
class Stem:
    key: str
    factor: float


@dataclass(frozen=True, slots=True)
class Token:
    key: str
    factor: float = 1.0


@dataclass(frozen=True, slots=True)
class Ref:
    glyph: str
    side: Literal["lsb", "rsb"]
    delta: float = 0.0


@dataclass(frozen=True, slots=True)
class Mirror:
    pass


@dataclass(frozen=True, slots=True)
class Optical:
    """Optical sidebearing match (implemented in P2-7)."""

    ref: str
    side: Literal["lsb", "rsb"]
    band: tuple[float, float] | None = None


Side = Abs | Stem | Token | Ref | Mirror | Optical


@dataclass(frozen=True, slots=True)
class Metrics:
    keys: Mapping[str, tuple[Side, Side]] = field(default_factory=dict)
    space: Side = field(default_factory=lambda: Token("space_advance"))
    pack: Literal["bbox", "slant-mid-x"] | None = None


@dataclass(frozen=True, slots=True)
class Kerning:
    classes: Sequence[KernClass] = ()
    pairs: Sequence[KernPair | ClassKernPair] = ()
    exceptions: Sequence[KernPair] = ()

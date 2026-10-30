"""Metrics keys engine (target-architecture §5.3).

Declarative ``Metrics`` / ``Kerning`` types plus ``resolve`` / ``pack`` /
``apply_metrics`` (extracted from starter ``spacing.py`` engines).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal

from typekernel.font.kerning import ClassKernPair, KernClass, KernPair
from typekernel.metrics.join import Join

__all__ = [
    "Abs",
    "Join",
    "Kerning",
    "Metrics",
    "Mirror",
    "Optical",
    "Ref",
    "Side",
    "Stem",
    "Token",
    "apply_kerning",
    "apply_metrics",
    "pack",
    "resolve",
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
    """Optical sidebearing match."""

    ref: str
    side: Literal["lsb", "rsb"]
    band: tuple[float, float] | None = None


Side = Abs | Stem | Token | Ref | Mirror | Optical


@dataclass(frozen=True, slots=True)
class Metrics:
    keys: Mapping[str, tuple[Side, Side]] = field(default_factory=dict)
    space: Side = field(default_factory=lambda: Token("space_advance"))
    pack: Literal["bbox", "slant-mid-x", "absolute"] | None = None
    # Fractions of x-height for italic silhouette packing (chancery-style).
    italic_pack_ys: tuple[float, ...] = ()
    join: Join | None = None
    """S3: when set, pair advances may align exit→entry (see metrics.join)."""

    def __post_init__(self) -> None:
        object.__setattr__(self, "keys", MappingProxyType(dict(self.keys)))
        object.__setattr__(self, "italic_pack_ys", tuple(self.italic_pack_ys))


@dataclass(frozen=True, slots=True)
class Kerning:
    classes: Sequence[KernClass] = ()
    pairs: Sequence[KernPair | ClassKernPair] = ()
    exceptions: Sequence[KernPair] = ()

from typekernel.metrics.applying import apply_kerning, apply_metrics
from typekernel.metrics.packing import pack
from typekernel.metrics.resolving import resolve

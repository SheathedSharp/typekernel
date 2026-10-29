"""Axis / master / instance declarations (target-architecture §10)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType

from typekernel.system import System

__all__ = ["Axis", "Instance", "MasterSpec"]


def _freeze_map(m: Mapping[str, float] | None) -> Mapping[str, float]:
    return MappingProxyType(dict(m or {}))


@dataclass(frozen=True, slots=True)
class Axis:
    """One variation axis (tag, range, optional avar map and STAT labels)."""

    tag: str
    name: str
    minimum: float
    default: float
    maximum: float
    map: Sequence[tuple[float, float]] = ()
    labels: Mapping[float, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "labels", MappingProxyType(dict(self.labels)))


@dataclass(frozen=True, slots=True)
class MasterSpec:
    """A designed master: name, design-space location, and System."""

    name: str
    location: Mapping[str, float]
    system: System

    def __post_init__(self) -> None:
        object.__setattr__(self, "location", _freeze_map(self.location))


@dataclass(frozen=True, slots=True)
class Instance:
    """A named instance at user coordinates (optional RIBBI style map)."""

    name: str
    location: Mapping[str, float]
    style_map: tuple[str, str] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "location", _freeze_map(self.location))

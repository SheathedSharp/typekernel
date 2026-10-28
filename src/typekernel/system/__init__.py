"""System — designer numeric table (ARCHITECTURE.md System)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Any

__all__ = ["Overshoot", "System", "Zones"]


@dataclass(frozen=True, slots=True)
class Zones:
    """Vertical alignment zones in design units."""

    x: float
    cap: float
    asc: float
    desc: float
    base: float = 0.0


@dataclass(frozen=True, slots=True)
class Overshoot:
    """How far extrema push past flat alignment zones."""

    round: float
    pointed: float


def _freeze_map(m: Mapping[str, float] | None) -> Mapping[str, float]:
    return MappingProxyType(dict(m or {}))


@dataclass(frozen=True, slots=True)
class System:
    """Designer numeric table — data only, no multi-site knobs.

    Forbidden by System: ``aperture`` / ``roundness`` and any single number that
    silently fans out into many geometries. Put derived relations in the
    project's own ``elements.py``.
    """

    upm: float
    zones: Zones
    overshoot: Overshoot
    stem: Mapping[str, float]
    tokens: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "stem", _freeze_map(self.stem))
        object.__setattr__(self, "tokens", _freeze_map(self.tokens))

    def tuned(self, **kw: Any) -> System:
        """Return a copy with the given fields replaced (shallow)."""
        return replace(self, **kw)

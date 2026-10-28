"""System / Zones / Overshoot — designer numeric table."""

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

    ``slant`` is first-class (not a project token): Δx per unit Δy lean so
    kern / audit / spacing can be italic-aware without reading ad-hoc tokens.
    ``0`` is upright. Positive leans right as y rises (true-italic construction
    lean — not :class:`~typekernel.axes.slant.ObliqueTransform` shear).

    Typed design intent (``Intent`` / ``Brief``) maps onto this table via
    :mod:`typekernel.system.intent` — prose stays in ``brief.md``; numbers here.
    """

    upm: float
    zones: Zones
    overshoot: Overshoot
    stem: Mapping[str, float]
    tokens: Mapping[str, float] = field(default_factory=dict)
    slant: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "stem", _freeze_map(self.stem))
        object.__setattr__(self, "tokens", _freeze_map(self.tokens))
        object.__setattr__(self, "slant", float(self.slant))

    def tuned(self, **kw: Any) -> System:
        """Return a copy with the given fields replaced (shallow)."""
        return replace(self, **kw)

    def slant_dx(self, y: float, *, y0: float = 0.0) -> float:
        """Horizontal shift from italic lean between ``y0`` and ``y``."""
        return float(self.slant) * (float(y) - float(y0))

    def map_xy(self, x: float, y: float, *, y0: float = 0.0) -> tuple[float, float]:
        """Map an upright ``(x, y)`` into slanted design space (y unchanged)."""
        return (float(x) + self.slant_dx(y, y0=y0), float(y))

    def stem_direction_deg(self) -> float:
        """Bearing of a constructed "vertical" stem (0°=+x, 90°=upright +y)."""
        import math

        return math.degrees(math.atan2(1.0, float(self.slant)))

    @property
    def is_italic(self) -> bool:
        return abs(float(self.slant)) > 1e-12

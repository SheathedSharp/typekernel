"""Spacing plugin protocol — suggestions only; never mutates contours.

Agents / ``tk spacing suggest`` may write results to a JSON file. Applying
values into ``Project.metrics`` / ``Kerning`` is a separate, explicit step.
This is **not** a complete Tracy optical-spacing workflow.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from typekernel.optics.context import OpticalContext
from typekernel.project.session import ProjectSession

__all__ = [
    "PairSuggestion",
    "SidebearingSuggestion",
    "SpacingContext",
    "SpacingPlugin",
    "SpacingSuggestions",
    "optical_context_from_system",
]


@dataclass(frozen=True, slots=True)
class SidebearingSuggestion:
    """Proposed LSB/RSB in design units (agent may copy into ``Metrics`` as Abs)."""

    glyph: str
    lsb: float
    rsb: float
    method: str
    note: str = ""


@dataclass(frozen=True, slots=True)
class PairSuggestion:
    """Proposed kern pair value (design units); not auto-applied."""

    left: str
    right: str
    value: float
    method: str
    note: str = ""


@dataclass(frozen=True, slots=True)
class SpacingSuggestions:
    sidebearings: tuple[SidebearingSuggestion, ...] = ()
    pairs: tuple[PairSuggestion, ...] = ()


@dataclass(frozen=True, slots=True)
class SpacingContext:
    """Inputs for a spacing plugin run."""

    session: ProjectSession
    optical: OpticalContext
    names: tuple[str, ...]
    master: str | None = None
    pair_seeds: tuple[tuple[str, str], ...] = ()


class SpacingPlugin(Protocol):
    """Opt-in spacing advisor.

    Implementations must not mutate glyph outlines or project Metrics.
    """

    id: str

    def suggest(self, ctx: SpacingContext) -> SpacingSuggestions: ...


def optical_context_from_system(system: object) -> OpticalContext:
    """Build :class:`OpticalContext` from a project :class:`~typekernel.system.System`."""
    upm = float(getattr(system, "upm", 1000.0) or 1000.0)
    zones = getattr(system, "zones", None)
    overshoot = getattr(system, "overshoot", None)
    x_height = float(getattr(zones, "x", 500.0) if zones is not None else 500.0)
    cap_height = float(getattr(zones, "cap", 700.0) if zones is not None else 700.0)
    ov_round = float(getattr(overshoot, "round", 12.0) if overshoot is not None else 12.0)
    ov_sharp = float(getattr(overshoot, "pointed", 0.0) if overshoot is not None else 0.0)
    return OpticalContext(
        units_per_em=upm,
        x_height=x_height,
        cap_height=cap_height,
        overshoot_round=ov_round,
        overshoot_sharp=ov_sharp,
    )

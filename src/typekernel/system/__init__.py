"""System — designer numeric table (ARCHITECTURE.md §9.7).

M1 only needs a typed handle for ``apply_slots`` fillers. Fields land in M2.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class System:
    """Placeholder numeric table; M2 adds Zones / Overshoot / stem tables."""

    name: str = "default"

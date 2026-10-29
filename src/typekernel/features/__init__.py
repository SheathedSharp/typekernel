"""OpenType feature declarations (target-architecture §11). Placeholder until P4."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

__all__ = ["Features"]


@dataclass(frozen=True, slots=True)
class Features:
    """Auto-generated + hand-written feature sources.

    ``fea_dir`` is relative to the project root when a string/Path is given.
    """

    fea_dir: str | Path | None = "features"
    extra: Sequence[str] = ()

"""OpenType features — suffix codegen + .fea assembly (target §11)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from typekernel.features.assemble import (
    FeatureSyntaxError,
    assemble_features,
    load_hand_fea,
    validate_fea,
)
from typekernel.features.generate import generate_features, parse_suffix

__all__ = [
    "FeatureSyntaxError",
    "Features",
    "assemble_features",
    "generate_features",
    "load_hand_fea",
    "parse_suffix",
    "validate_fea",
]


@dataclass(frozen=True, slots=True)
class Features:
    """Auto-generated + hand-written feature sources.

    ``fea_dir`` is relative to the project root when a string/Path is given.
    """

    fea_dir: str | Path | None = "features"
    extra: Sequence[str] = ()

"""Spacing plugins — opt-in suggestions; Project.metrics remains the source of truth.

Minimal Protocol + two heuristics (bbox rhythm, optical air). Full Tracy /
gray-value optical spacing workflow is **not** claimed complete.
"""

from __future__ import annotations

from typekernel.plugins.spacing.bbox_rhythm import BBoxRhythmPlugin
from typekernel.plugins.spacing.optical_air import OpticalAirPlugin
from typekernel.plugins.spacing.protocol import (
    PairSuggestion,
    SidebearingSuggestion,
    SpacingContext,
    SpacingPlugin,
    SpacingSuggestions,
    optical_context_from_system,
)
from typekernel.plugins.spacing.run import (
    default_spacing_plugin,
    run_spacing_plugin,
    write_spacing_suggestions,
)

__all__ = [
    "BBoxRhythmPlugin",
    "OpticalAirPlugin",
    "PairSuggestion",
    "SidebearingSuggestion",
    "SpacingContext",
    "SpacingPlugin",
    "SpacingSuggestions",
    "default_spacing_plugin",
    "optical_context_from_system",
    "run_spacing_plugin",
    "write_spacing_suggestions",
]

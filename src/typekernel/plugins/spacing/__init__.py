"""Spacing plugins — opt-in suggestions; Project.metrics remains the source of truth.

Protocol + heuristics (bbox rhythm, optical air, multi-band Tracy silhouette).
Apply path writes Abs into spacing.py only with explicit ``--write``.
Full Tracy gray-value optical spacing workflow is **not** claimed complete.
"""

from __future__ import annotations

from typekernel.plugins.spacing.apply import (
    ApplyPlan,
    ApplyPlanEntry,
    ApplyResult,
    build_apply_plan,
    metrics_after_plan,
    run_apply,
    write_apply_plan,
    write_spacing_py_abs,
)
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
from typekernel.plugins.spacing.tracy_bands import TracyBandPlugin

__all__ = [
    "ApplyPlan",
    "ApplyPlanEntry",
    "ApplyResult",
    "BBoxRhythmPlugin",
    "OpticalAirPlugin",
    "PairSuggestion",
    "SidebearingSuggestion",
    "SpacingContext",
    "SpacingPlugin",
    "SpacingSuggestions",
    "TracyBandPlugin",
    "build_apply_plan",
    "default_spacing_plugin",
    "metrics_after_plan",
    "optical_context_from_system",
    "run_apply",
    "run_spacing_plugin",
    "write_apply_plan",
    "write_spacing_py_abs",
    "write_spacing_suggestions",
]

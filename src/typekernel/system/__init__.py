"""System — designer numeric table (ARCHITECTURE.md System)."""

from __future__ import annotations

from typekernel.system.intent import (
    Brief,
    ContrastFeel,
    Intent,
    IntentMismatch,
    OpennessFeel,
    SlantFeel,
    WeightFeel,
    apply_intent,
    check_intent,
    pen_defaults_for,
    system_from_intent,
)
from typekernel.system.lint import (
    CONTROL_WIDTH_TOKENS,
    lint_per_glyph_metric_tokens,
)
from typekernel.system.table import Overshoot, System, Zones
from typekernel.system.traits import TRAITS, UnknownTraitError, validate_traits

__all__ = [
    "CONTROL_WIDTH_TOKENS",
    "TRAITS",
    "Brief",
    "ContrastFeel",
    "Intent",
    "IntentMismatch",
    "OpennessFeel",
    "Overshoot",
    "SlantFeel",
    "System",
    "UnknownTraitError",
    "WeightFeel",
    "Zones",
    "apply_intent",
    "check_intent",
    "lint_per_glyph_metric_tokens",
    "pen_defaults_for",
    "system_from_intent",
    "validate_traits",
]

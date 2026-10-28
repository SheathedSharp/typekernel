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
from typekernel.system.table import Overshoot, System, Zones

__all__ = [
    "Brief",
    "ContrastFeel",
    "Intent",
    "IntentMismatch",
    "OpennessFeel",
    "Overshoot",
    "SlantFeel",
    "System",
    "WeightFeel",
    "Zones",
    "apply_intent",
    "check_intent",
    "pen_defaults_for",
    "system_from_intent",
]

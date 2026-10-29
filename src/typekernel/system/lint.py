"""System token lint (target-architecture §5.1)."""

from __future__ import annotations

import re

from typekernel.system.table import System

__all__ = [
    "CONTROL_WIDTH_TOKENS",
    "PER_GLYPH_METRIC_TOKEN",
    "lint_per_glyph_metric_tokens",
]

# Global control-word widths that remain on System.tokens (§5.1).
CONTROL_WIDTH_TOKENS = frozenset({"n_width", "o_width", "H_width", "O_width"})

PER_GLYPH_METRIC_TOKEN = re.compile(r"^(.+)_(width|advance)$")


def lint_per_glyph_metric_tokens(system: System) -> list[str]:
    """Return token names that look like per-glyph width/advance tables.

    Control widths ``n_width`` / ``o_width`` / ``H_width`` / ``O_width`` are
    allowed. Everything else matching ``<name>_(width|advance)`` should move
    to project data (e.g. ``elements.WIDTHS``) or metrics keys.
    """
    bad: list[str] = []
    for key in system.tokens:
        if not PER_GLYPH_METRIC_TOKEN.match(str(key)):
            continue
        if str(key) in CONTROL_WIDTH_TOKENS:
            continue
        bad.append(str(key))
    return sorted(bad)

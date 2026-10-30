"""Run a spacing plugin and serialize suggestions (no Metrics mutation)."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from typekernel.plugins.spacing.bbox_rhythm import BBoxRhythmPlugin
from typekernel.plugins.spacing.protocol import (
    SpacingContext,
    SpacingPlugin,
    SpacingSuggestions,
    optical_context_from_system,
)
from typekernel.project.session import ProjectSession

__all__ = [
    "default_spacing_plugin",
    "run_spacing_plugin",
    "write_spacing_suggestions",
]


def default_spacing_plugin() -> SpacingPlugin:
    """Default opt-in advisor: bbox / x-height rhythm (not full Tracy)."""
    return BBoxRhythmPlugin()


def run_spacing_plugin(
    session: ProjectSession,
    plugin: SpacingPlugin | None = None,
    *,
    master: str | None = None,
    names: Sequence[str] | None = None,
) -> SpacingSuggestions:
    """Collect suggestions for ``names`` (default: all project specs)."""
    plug = plugin if plugin is not None else default_spacing_plugin()
    system = session.project.system
    if master is not None:
        by = {m.name: m for m in session.project.masters}
        if master in by:
            system = by[master].system
    glyph_names = tuple(names) if names is not None else tuple(sorted(session.specs()))
    ctx = SpacingContext(
        session=session,
        optical=optical_context_from_system(system),
        names=glyph_names,
        master=master,
    )
    return plug.suggest(ctx)


def write_spacing_suggestions(
    suggestions: SpacingSuggestions,
    path: str | Path,
    *,
    plugin_id: str,
) -> Path:
    """Write JSON agents can review before editing ``Project.metrics``."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "note": (
            "Spacing suggestions from plugins.spacing — review before copying "
            "into Project.metrics as Abs(...). Not auto-applied; not full Tracy."
        ),
        "plugin": plugin_id,
        "sidebearings": [asdict(s) for s in suggestions.sidebearings],
        "pairs": [asdict(p) for p in suggestions.pairs],
        "metrics_hint": {
            "example": "Abs(lsb), Abs(rsb) in Metrics.keys[glyph]",
        },
    }
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out

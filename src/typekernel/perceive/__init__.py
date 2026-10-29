"""Perceive — live / shipped rendering, edit views, and glyph explain (target §6)."""

from __future__ import annotations

from typekernel.perceive.explain import GlyphReport, explain
from typekernel.perceive.render import LiveGlyph, render_live
from typekernel.perceive.topology import Topology, measure_topology
from typekernel.perceive.views import (
    SeeResult,
    context_view,
    diff_view,
    edit_view,
    overlay_view,
    reference_view,
)

__all__ = [
    "GlyphReport",
    "LiveGlyph",
    "SeeResult",
    "Topology",
    "context_view",
    "diff_view",
    "edit_view",
    "explain",
    "measure_topology",
    "overlay_view",
    "reference_view",
    "render_live",
]

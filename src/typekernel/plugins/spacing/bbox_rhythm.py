"""Minimal Tracy-adjacent spacing plugin: bbox / x-height rhythm sidebearings.

Uses :func:`typekernel.optics.sidebearing.suggest_sidebearings` — a documented
heuristic, not gray-value Tracy. Pair suggestions are left empty; use
``tk kern suggest`` / optical pair fit for kerning.
"""

from __future__ import annotations

from typekernel.optics.sidebearing import suggest_sidebearings
from typekernel.plugins.spacing.protocol import (
    SidebearingSuggestion,
    SpacingContext,
    SpacingSuggestions,
)

__all__ = ["BBoxRhythmPlugin"]


class BBoxRhythmPlugin:
    """Equal LSB/RSB from ink width vs x-height (optics bbox rhythm)."""

    id = "bbox_rhythm"

    def suggest(self, ctx: SpacingContext) -> SpacingSuggestions:
        out: list[SidebearingSuggestion] = []
        for name in ctx.names:
            if name not in ctx.session.specs():
                continue
            draft = ctx.session.evaluate(name, master=ctx.master)
            outline = draft.drawing.outline()
            if not outline.contours:
                continue
            lsb, rsb = suggest_sidebearings(outline, ctx.optical)
            out.append(
                SidebearingSuggestion(
                    glyph=name,
                    lsb=float(round(lsb, 1)),
                    rsb=float(round(rsb, 1)),
                    method=self.id,
                    note="heuristic bbox rhythm; refine by eye before Metrics Abs",
                )
            )
        return SpacingSuggestions(sidebearings=tuple(out), pairs=())

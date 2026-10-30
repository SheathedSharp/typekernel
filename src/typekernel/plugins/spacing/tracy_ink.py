"""Partial Tracy ink-density sidebearing plugin (scanline column fractions).

Uses :func:`typekernel.optics.space.suggest_sidebearings_ink_density`.
Not a bitmap / stem-band gray Tracy model — outer-column ink fractions only.
"""

from __future__ import annotations

from typekernel.optics.space import suggest_sidebearings_ink_density
from typekernel.plugins.spacing.protocol import (
    SidebearingSuggestion,
    SpacingContext,
    SpacingSuggestions,
)

__all__ = ["TracyInkPlugin"]


class TracyInkPlugin:
    """LSB/RSB from side-column ink density (partial Tracy gray cue)."""

    id = "tracy_ink"

    def suggest(self, ctx: SpacingContext) -> SpacingSuggestions:
        out: list[SidebearingSuggestion] = []
        for name in ctx.names:
            if name not in ctx.session.specs():
                continue
            glyph = ctx.session.glyph(name, master=ctx.master)
            if not glyph.outline.contours:
                continue
            lsb, rsb = suggest_sidebearings_ink_density(glyph, ctx.optical)
            out.append(
                SidebearingSuggestion(
                    glyph=name,
                    lsb=float(round(lsb, 1)),
                    rsb=float(round(rsb, 1)),
                    method=self.id,
                    note=(
                        "scanline side-column ink fraction; "
                        "not bitmap gray / full Tracy; not auto-applied"
                    ),
                )
            )
        return SpacingSuggestions(sidebearings=tuple(out), pairs=())

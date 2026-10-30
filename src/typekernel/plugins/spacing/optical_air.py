"""Optional silhouette-air sidebearing suggestions (optics.space).

Still not full Tracy: no stem-band gray model, no auto Metrics write.
"""

from __future__ import annotations

from typekernel.optics.space import suggest_sidebearings_optical
from typekernel.plugins.spacing.protocol import (
    SidebearingSuggestion,
    SpacingContext,
    SpacingSuggestions,
)

__all__ = ["OpticalAirPlugin"]


class OpticalAirPlugin:
    """LSB/RSB from silhouette whitespace vs target air budget."""

    id = "optical_air"

    def suggest(self, ctx: SpacingContext) -> SpacingSuggestions:
        out: list[SidebearingSuggestion] = []
        for name in ctx.names:
            if name not in ctx.session.specs():
                continue
            glyph = ctx.session.glyph(name, master=ctx.master)
            if not glyph.outline.contours:
                continue
            lsb, rsb = suggest_sidebearings_optical(glyph, ctx.optical)
            out.append(
                SidebearingSuggestion(
                    glyph=name,
                    lsb=float(round(lsb, 1)),
                    rsb=float(round(rsb, 1)),
                    method=self.id,
                    note="silhouette air heuristic; not auto-applied",
                )
            )
        return SpacingSuggestions(sidebearings=tuple(out), pairs=())

"""Partial Tracy-style multi-band silhouette sidebearing plugin.

Uses :func:`typekernel.optics.space.suggest_sidebearings_tracy_bands`.
Not a gray-value / bitmap Tracy model — band-weighted silhouette air only.
Optional kern pair suggestions delegate to ``metrics.kern_suggest``.
"""

from __future__ import annotations

from typekernel.optics.space import suggest_sidebearings_tracy_bands
from typekernel.plugins.spacing.protocol import (
    PairSuggestion,
    SidebearingSuggestion,
    SpacingContext,
    SpacingSuggestions,
)

__all__ = ["TracyBandPlugin"]


class TracyBandPlugin:
    """Multi-band silhouette air (partial Tracy); optional kern pairs."""

    id = "tracy_bands"

    def __init__(self, *, include_pairs: bool = False, target_gap: float = 24.0) -> None:
        self.include_pairs = bool(include_pairs)
        self.target_gap = float(target_gap)

    def suggest(self, ctx: SpacingContext) -> SpacingSuggestions:
        side: list[SidebearingSuggestion] = []
        for name in ctx.names:
            if name not in ctx.session.specs():
                continue
            glyph = ctx.session.glyph(name, master=ctx.master)
            if not glyph.outline.contours:
                continue
            lsb, rsb = suggest_sidebearings_tracy_bands(glyph, ctx.optical)
            side.append(
                SidebearingSuggestion(
                    glyph=name,
                    lsb=float(round(lsb, 1)),
                    rsb=float(round(rsb, 1)),
                    method=self.id,
                    note="multi-band silhouette air; not gray-value Tracy; not auto-applied",
                )
            )
        pairs: list[PairSuggestion] = []
        if self.include_pairs:
            from typekernel.metrics.kern_suggest import suggest_kern_pairs

            for ks in suggest_kern_pairs(
                ctx.session, master=ctx.master, target_gap=self.target_gap
            ):
                pairs.append(
                    PairSuggestion(
                        left=ks.left,
                        right=ks.right,
                        value=float(ks.suggested),
                        method="kern_suggest",
                        note=ks.reason,
                    )
                )
        return SpacingSuggestions(sidebearings=tuple(side), pairs=tuple(pairs))

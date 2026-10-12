"""Spacing, sidebearings, and minimal kerning for composed glyphs.

Coding agents need more than raw outlines: advance widths, tracking, and a
small kerning-pair table so a word like ``zayju`` can be laid out without
hand-tuned pixel offsets.
"""

from __future__ import annotations

from dataclasses import dataclass

from typekernel.geo.layout import layout_x_positions
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext


@dataclass(frozen=True, slots=True)
class KernPair:
    """One pairwise kerning adjustment in design units.

    ``value`` is added to the advance *between* ``left`` and ``right``
    (negative pulls them closer). Glyph names are single characters or
    PostScript-style names — agents should be consistent within one table.
    """

    left: str
    right: str
    value: float


@dataclass(frozen=True, slots=True)
class KernTable:
    """Minimal kerning dictionary keyed by ``(left, right)``."""

    pairs: tuple[KernPair, ...] = ()

    def lookup(self, left: str, right: str) -> float:
        for p in self.pairs:
            if p.left == left and p.right == right:
                return p.value
        return 0.0

    def with_pair(self, left: str, right: str, value: float) -> KernTable:
        """Return a new table with one pair added or replaced."""
        kept = [p for p in self.pairs if not (p.left == left and p.right == right)]
        kept.append(KernPair(left, right, value))
        return KernTable(tuple(kept))


def default_sans_kern() -> KernTable:
    """A tiny starter kerning set for geometric lowercase demos."""
    return KernTable(
        (
            KernPair("a", "y", -18.0),
            KernPair("y", "j", -10.0),
            KernPair("z", "a", -8.0),
            KernPair("j", "u", -4.0),
            KernPair("a", "v", -16.0),
            KernPair("v", "a", -16.0),
            KernPair("T", "a", -28.0),
            KernPair("L", "T", -20.0),
        )
    )


def sidebearing_for_width(ctx: DesignContext, ink_width: float) -> float:
    """Heuristic sidebearing from context rhythm and glyph ink width."""
    sb = max(
        0.04 * ctx.units_per_em,
        ctx.sidebearing_ratio * ctx.x_height,
    )
    scale = ctx.x_height / max(ink_width, 1.0)
    scale = max(0.90, min(1.10, scale))
    return sb * scale


def layout_glyphs(
    glyphs: list[ComposedGlyph],
    names: list[str] | None = None,
    *,
    tracking: float | None = None,
    kerning: KernTable | None = None,
    origin_x: float = 0.0,
) -> list[float]:
    """Return pen-x positions for each glyph, applying tracking and kerning.

    If ``names`` is omitted, kerning is skipped (tracking still applies).
    """
    if not glyphs:
        return []
    ctx = glyphs[0].context
    track = ctx.tracking if tracking is None else tracking
    advances = [g.advance for g in glyphs]
    xs = layout_x_positions(advances, tracking=track, origin_x=origin_x)
    if kerning is None or names is None:
        return xs
    if len(names) != len(glyphs):
        raise ValueError("names length must match glyphs")
    # Rebuild with pairwise kern inserted between glyphs.
    out: list[float] = []
    x = origin_x
    for i, (g, name) in enumerate(zip(glyphs, names)):
        out.append(x)
        x += g.advance
        if i < len(glyphs) - 1:
            x += track
            x += kerning.lookup(name, names[i + 1])
    return out

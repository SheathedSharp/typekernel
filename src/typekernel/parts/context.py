"""Shared design rhythm for composed glyphs (Three.js-style scene params).

Every letter in a family should share one :class:`DesignContext` so stems,
counters, overshoot and tracking stay consistent — like a Three.js scene
sharing one unit scale and material, rather than hard-coding each mesh.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DesignContext:
    """Family-wide parameters for assembling glyphs from parts.

    Attributes:
        units_per_em: Em square (typically 1000).
        x_height: Height of flat lowercase tops (``z``, ``x``).
        cap_height: Height of flat uppercase tops.
        descender: Lowest extent for ``y``, ``j``, ``g`` (usually negative).
        stem: Vertical stem thickness (design units).
        contrast: Horizontal-to-vertical stroke ratio. ``1.0`` is even colour;
            values below 1 make horizontals thinner than stems.
        overshoot: How far round extrema push past flat alignment zones.
        roundness: Softness of joins / terminals in ``0..1`` (maps to fillet
            radius as a fraction of ``stem``).
        tracking: Extra space inserted between glyphs when laying out a word.
        sidebearing_ratio: Base sidebearing as a fraction of ``x_height``.
    """

    units_per_em: float = 1000.0
    x_height: float = 520.0
    cap_height: float = 700.0
    descender: float = -200.0
    stem: float = 76.0
    contrast: float = 1.0
    overshoot: float = 12.0
    roundness: float = 0.35
    tracking: float = 8.0
    sidebearing_ratio: float = 0.10

    @property
    def thin(self) -> float:
        """Horizontal / thin stroke thickness from ``stem * contrast``."""
        return self.stem * self.contrast

    @property
    def join_radius(self) -> float:
        """Fillet radius derived from ``roundness * stem``."""
        return max(0.0, self.roundness * self.stem)

    @property
    def baseline(self) -> float:
        return 0.0

    @classmethod
    def geometric_sans(cls) -> DesignContext:
        """Neo-grotesque defaults: even colour, soft joins, high x-height."""
        return cls(
            units_per_em=1000.0,
            x_height=520.0,
            cap_height=700.0,
            descender=-210.0,
            stem=72.0,
            contrast=0.98,
            overshoot=12.0,
            roundness=0.48,
            tracking=10.0,
            sidebearing_ratio=0.11,
        )

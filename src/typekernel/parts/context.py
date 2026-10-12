"""Shared design rhythm for composed glyphs (Three.js-style scene params).

Every letter in a family should share one :class:`DesignContext` so stems,
counters, overshoot and tracking stay consistent — like a Three.js scene
sharing one unit scale and material, rather than hard-coding each mesh.

Presets are starting points for coding agents; tune fields per family.
"""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class DesignContext:
    """Family-wide parameters for assembling glyphs from parts.

    Attributes:
        units_per_em: Em square (typically 1000).
        x_height: Height of flat lowercase tops (``z``, ``x``).
        cap_height: Height of flat uppercase tops.
        ascender: Highest extent for ``b``, ``d``, ``h``, ``l`` (often ≈ cap).
        descender: Lowest extent for ``y``, ``j``, ``g`` (usually negative).
        stem: Vertical stem thickness (design units).
        contrast: Horizontal-to-vertical stroke ratio. ``1.0`` is even colour;
            values below 1 make horizontals thinner than stems.
        overshoot: How far round extrema push past flat alignment zones.
        roundness: Softness of joins / terminals in ``0..1`` (maps to fillet
            radius as a fraction of ``stem``).
        tracking: Extra space inserted between glyphs when laying out a word.
        sidebearing_ratio: Base sidebearing as a fraction of ``x_height``.
        aperture: How open counters / terminals feel (``0..1``); recipes may
            widen gaps in ``e``, ``c``, ``s`` from this knob.
    """

    units_per_em: float = 1000.0
    x_height: float = 520.0
    cap_height: float = 700.0
    ascender: float = 740.0
    descender: float = -200.0
    stem: float = 76.0
    contrast: float = 1.0
    overshoot: float = 12.0
    roundness: float = 0.35
    tracking: float = 8.0
    sidebearing_ratio: float = 0.10
    aperture: float = 0.55

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

    def tuned(self, **kwargs: float) -> DesignContext:
        """Return a copy with selected fields overridden (agent-friendly)."""
        return replace(self, **kwargs)

    @classmethod
    def geometric_sans(cls) -> DesignContext:
        """Neo-grotesque defaults: even colour, soft joins, high x-height.

        Rhythm roughly mirrors a modern geometric sans (stem ≈ 0.09 em,
        x-height ≈ 0.54 em, modest overshoot, tight tracking).
        """
        return cls(
            units_per_em=1000.0,
            x_height=540.0,
            cap_height=720.0,
            ascender=750.0,
            descender=-240.0,
            stem=90.0,
            contrast=1.0,
            overshoot=11.0,
            roundness=0.28,
            tracking=0.0,
            sidebearing_ratio=0.08,
            aperture=0.55,
        )

    @classmethod
    def humanist_sans(cls) -> DesignContext:
        """Calligraphic tilt: more contrast, open aperture, warmer joins."""
        return cls(
            units_per_em=1000.0,
            x_height=500.0,
            cap_height=700.0,
            ascender=760.0,
            descender=-220.0,
            stem=70.0,
            contrast=0.82,
            overshoot=14.0,
            roundness=0.55,
            tracking=6.0,
            sidebearing_ratio=0.10,
            aperture=0.72,
        )

    @classmethod
    def mono(cls) -> DesignContext:
        """Monospace-friendly: heavier stems, tighter tracking, square feel."""
        return cls(
            units_per_em=1000.0,
            x_height=540.0,
            cap_height=700.0,
            ascender=740.0,
            descender=-200.0,
            stem=88.0,
            contrast=1.0,
            overshoot=8.0,
            roundness=0.22,
            tracking=0.0,
            sidebearing_ratio=0.14,
            aperture=0.45,
        )

    @classmethod
    def display(cls) -> DesignContext:
        """Display / poster: thinner stems, larger overshoot, loose tracking."""
        return cls(
            units_per_em=1000.0,
            x_height=480.0,
            cap_height=720.0,
            ascender=780.0,
            descender=-240.0,
            stem=52.0,
            contrast=0.90,
            overshoot=18.0,
            roundness=0.60,
            tracking=18.0,
            sidebearing_ratio=0.12,
            aperture=0.65,
        )

    @classmethod
    def paper_ink(cls) -> DesignContext:
        """Paper-first book weight: durable stems, open counters, more ink."""
        return cls(
            units_per_em=1000.0,
            x_height=530.0,
            cap_height=710.0,
            ascender=760.0,
            descender=-230.0,
            stem=100.0,
            contrast=1.0,
            overshoot=14.0,
            roundness=0.30,
            tracking=0.0,
            sidebearing_ratio=0.09,
            aperture=0.60,
        )

    @classmethod
    def code_clear(cls) -> DesignContext:
        """Coding-first: tall x-height, even stems, generous even sidebearings."""
        return cls(
            units_per_em=1000.0,
            x_height=565.0,
            cap_height=720.0,
            ascender=770.0,
            descender=-220.0,
            stem=86.0,
            contrast=1.0,
            overshoot=9.0,
            roundness=0.16,
            tracking=0.0,
            sidebearing_ratio=0.12,
            aperture=0.50,
        )

    @classmethod
    def open_print(cls) -> DesignContext:
        """Print-open: soft joins, wide aperture, airy counters for paper."""
        return cls(
            units_per_em=1000.0,
            x_height=545.0,
            cap_height=715.0,
            ascender=765.0,
            descender=-235.0,
            stem=92.0,
            contrast=0.98,
            overshoot=16.0,
            roundness=0.48,
            tracking=0.0,
            sidebearing_ratio=0.10,
            aperture=0.72,
        )

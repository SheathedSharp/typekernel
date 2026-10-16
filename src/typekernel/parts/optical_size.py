"""Optical-size (``opsz``) designed deltas for text ↔ display masters.

Small sizes need slightly heavier stems, opener counters, and tighter rhythm;
display sizes go thinner, looser, and more overshoot. Agents should draw each
``opsz`` master from :func:`context_for_opsz`, not scale outlines.
"""

from __future__ import annotations

from typekernel.parts.context import DesignContext

__all__ = [
    "DEFAULT_DISPLAY_OPSZ",
    "DEFAULT_TEXT_OPSZ",
    "context_for_opsz",
    "lerp",
]

DEFAULT_TEXT_OPSZ = 14.0
DEFAULT_DISPLAY_OPSZ = 72.0


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolate ``a``→``b`` by ``t`` in ``[0, 1]``."""
    return a + (b - a) * t


def context_for_opsz(
    base: DesignContext,
    opsz: float,
    *,
    text_opsz: float = DEFAULT_TEXT_OPSZ,
    display_opsz: float = DEFAULT_DISPLAY_OPSZ,
) -> DesignContext:
    """Return a :class:`DesignContext` tuned for optical size ``opsz``.

    ``opsz`` is in typographic points (OpenType ``opsz`` user coordinates).
    Values at or below ``text_opsz`` use the text endpoint; at or above
    ``display_opsz`` use the display endpoint; in between, fields lerp.
    """
    if display_opsz <= text_opsz:
        raise ValueError("display_opsz must be greater than text_opsz")
    t = (float(opsz) - text_opsz) / (display_opsz - text_opsz)
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)

    # Text (t=0): heavier, opener, tighter. Display (t=1): lighter, looser, airier.
    stem = lerp(base.stem * 1.10, base.stem * 0.86, t)
    tracking = lerp(max(0.0, base.tracking - 4.0), base.tracking + 14.0, t)
    sidebearing_ratio = lerp(
        min(0.18, base.sidebearing_ratio + 0.025),
        max(0.06, base.sidebearing_ratio - 0.02),
        t,
    )
    aperture = lerp(min(1.0, base.aperture + 0.10), base.aperture, t)
    overshoot = lerp(base.overshoot * 0.80, base.overshoot * 1.40, t)
    x_height = lerp(base.x_height * 1.025, base.x_height, t)
    contrast = lerp(base.contrast, max(0.72, base.contrast * 0.92), t)
    return base.tuned(
        stem=stem,
        tracking=tracking,
        sidebearing_ratio=sidebearing_ratio,
        aperture=aperture,
        overshoot=overshoot,
        x_height=x_height,
        contrast=contrast,
    )

"""Counter and bowl relief as stem weight approaches black (interpolation-safe).

Relief widens counters and bowl width floors using stem-driven fractions only —
no boolean topology changes.
"""

from __future__ import annotations

from typekernel.parts.control import NMetrics, OMetrics

STEM_REF = 76.0
STEM_BLACK = 220.0

__all__ = [
    "STEM_BLACK",
    "STEM_REF",
    "figure_width_floor",
    "min_bowl_stems",
    "relieve_n_o",
    "stem_weight_fraction",
]


def stem_weight_fraction(stem: float, *, ref: float = STEM_REF, black: float = STEM_BLACK) -> float:
    """``0`` at regular weight, ``1`` at ``black`` (linear clamp)."""
    threshold = ref * 1.12
    if stem <= threshold:
        return 0.0
    return min(1.0, (stem - threshold) / max(black - threshold, 1.0))


def relieve_n_o(n: NMetrics, o: OMetrics, stem: float) -> tuple[NMetrics, OMetrics]:
    """Widen ``n`` counter and ``o`` bowl for heavy stems."""
    t = stem_weight_fraction(stem)
    if t <= 0.0:
        return n, o
    return (
        n.tuned(counter=n.counter + t * (20.0 + 0.10 * n.counter)),
        o.tuned(
            rx=o.rx + t * (24.0 + 0.06 * o.rx),
            ry=o.ry + t * (8.0 + 0.04 * o.ry),
        ),
    )


def min_bowl_stems(stem: float) -> float:
    """Minimum half-bowl width in cap-stem units (``P`` ``R`` ``B`` …)."""
    return 2.3 + stem_weight_fraction(stem) * 1.05


def figure_width_floor(stem: float) -> float:
    """Minimum figure ink width at cap height for round digits."""
    return (2.6 + stem_weight_fraction(stem) * 0.55) * stem

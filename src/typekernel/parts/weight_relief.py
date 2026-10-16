"""Counter and bowl relief as stem weight approaches black (interpolation-safe).

Relief widens counters and bowl width floors using stem-driven fractions only —
no boolean topology changes.
"""

from __future__ import annotations

from typekernel.parts.control import NMetrics, OMetrics

STEM_REF = 76.0
STEM_BLACK = 220.0
STEM_RELIEF_ONSET = 85.0
COUNTER_GAP_FLOOR_OVER_STEM = 0.08  # R8 lint floor (see test_gate_thresholds_locked)
COUNTER_GAP_FLOOR_BASE = 2.5

__all__ = [
    "COUNTER_GAP_FLOOR_BASE",
    "COUNTER_GAP_FLOOR_OVER_STEM",
    "STEM_BLACK",
    "STEM_REF",
    "STEM_RELIEF_ONSET",
    "counter_gap_floor",
    "figure_width_floor",
    "m_counter_scale",
    "min_bowl_stems",
    "relieve_n_o",
    "stem_weight_fraction",
]


def stem_weight_fraction(stem: float, *, ref: float = STEM_REF, black: float = STEM_BLACK) -> float:
    """``0`` at regular weight, ``1`` at ``black`` (linear clamp)."""
    threshold = ref * 1.05
    if stem <= threshold:
        return 0.0
    return min(1.0, (stem - threshold) / max(black - threshold, 1.0))


def relieve_n_o(n: NMetrics, o: OMetrics, stem: float) -> tuple[NMetrics, OMetrics]:
    """Widen ``n`` counter and ``o`` bowl for heavy stems."""
    t = stem_weight_fraction(stem)
    if t <= 0.0:
        return n, o
    return (
        n.tuned(counter=n.counter + t * (24.0 + 0.12 * n.counter)),
        o.tuned(
            rx=o.rx + t * (28.0 + 0.08 * o.rx),
            ry=o.ry + t * (10.0 + 0.05 * o.ry),
        ),
    )


def counter_gap_floor(stem: float) -> float:
    """Minimum counter pinch (font units) for R8 at this stem weight."""
    return COUNTER_GAP_FLOOR_OVER_STEM * stem + COUNTER_GAP_FLOOR_BASE


def m_counter_scale(stem: float, *, base: float = 0.92) -> float:
    """``m`` arch counter scale widens slightly toward black."""
    return base + 0.14 * stem_weight_fraction(stem)


def min_bowl_stems(stem: float) -> float:
    """Minimum half-bowl width in cap-stem units (``P`` ``R`` ``B`` …)."""
    return 2.3 + stem_weight_fraction(stem) * 1.05


def figure_width_floor(stem: float) -> float:
    """Minimum figure ink width at cap height for round digits."""
    return (2.6 + stem_weight_fraction(stem) * 0.55) * stem

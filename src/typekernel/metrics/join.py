"""S3 join strategy — align A.exit → B.entry; rhythm / pair measures."""

from __future__ import annotations

import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from typekernel.font.glyph import Anchor, Glyph

__all__ = [
    "ENTRY",
    "EXIT",
    "Join",
    "JoinPairMeasure",
    "anchor_by_name",
    "gap_cv",
    "join_advance",
    "measure_join_pair",
    "measure_text_joins",
]

ENTRY = "entry"
EXIT = "exit"


@dataclass(frozen=True, slots=True)
class Join:
    """Metrics join strategy + diagnose thresholds (S3).

    When present on :class:`~typekernel.metrics.Metrics`, pair advances may be
    derived by aligning the left glyph's ``exit`` to the right glyph's
    ``entry``. Diagnose uses the same thresholds for Δy / tangent / width /
    gap rhythm.
    """

    max_dy: float = 20.0
    max_angle_delta: float = 25.0
    max_width_delta: float = 30.0
    max_gap_cv: float = 0.35
    gap_outlier: float = 48.0
    """Absolute |gap| (du) that flags a spacing outlier for a joined pair."""


@dataclass(frozen=True, slots=True)
class JoinPairMeasure:
    left: str
    right: str
    dy: float
    angle_delta: float
    width_delta: float
    gap: float
    """Horizontal residual after placing right at ``advance`` (0 = perfect join)."""

    advance: float
    """Derived advance that aligns exit→entry in x."""

    has_join: bool
    """True when both entry and exit anchors were present."""


def anchor_by_name(glyph: Glyph, name: str) -> Anchor | None:
    for a in glyph.anchors:
        if a.name == name:
            return a
    return None


def join_advance(exit_a: Anchor, entry_b: Anchor) -> float:
    """Advance that places ``entry_b`` on ``exit_a`` in x."""
    return float(exit_a.x) - float(entry_b.x)


def _angle_delta(a: float | None, b: float | None) -> float:
    if a is None or b is None:
        return 0.0
    d = abs(float(a) - float(b)) % 360.0
    return min(d, 360.0 - d)


def _width_delta(a: float | None, b: float | None) -> float:
    if a is None or b is None:
        return 0.0
    return abs(float(a) - float(b))


def measure_join_pair(
    left: Glyph,
    right: Glyph,
    *,
    advance: float | None = None,
) -> JoinPairMeasure:
    """Measure one adjacent pair; ``has_join`` False when anchors missing."""
    ex = anchor_by_name(left, EXIT)
    en = anchor_by_name(right, ENTRY)
    if ex is None or en is None:
        adv = float(advance if advance is not None else left.advance)
        # Fallback bbox-ish gap: right origin at adv → ink not modeled here.
        gap = adv - float(left.advance) if advance is not None else 0.0
        return JoinPairMeasure(
            left=left.name,
            right=right.name,
            dy=0.0,
            angle_delta=0.0,
            width_delta=0.0,
            gap=float(gap),
            advance=adv,
            has_join=False,
        )
    adv = float(advance if advance is not None else join_advance(ex, en))
    # After placing right at x=adv: exit_world_x = ex.x, entry_world_x = adv+en.x
    gap = (adv + float(en.x)) - float(ex.x)
    dy = abs(float(ex.y) - float(en.y))
    return JoinPairMeasure(
        left=left.name,
        right=right.name,
        dy=dy,
        angle_delta=_angle_delta(ex.angle, en.angle),
        width_delta=_width_delta(ex.width, en.width),
        gap=gap,
        advance=adv,
        has_join=True,
    )


def gap_cv(gaps: Sequence[float]) -> float:
    """Coefficient of variation of inter-letter |gaps|.

    Uses mean absolute gap as the scale so near-perfect joins (all ~0)
    report 0, while uneven gappy joins report a high ratio.
    """
    vals = [float(g) for g in gaps]
    if len(vals) < 2:
        return 0.0
    mean_abs = statistics.fmean(abs(v) for v in vals)
    stdev = float(statistics.pstdev(vals))
    if mean_abs < 1e-9:
        return 0.0
    return stdev / mean_abs


def measure_text_joins(
    glyphs: Mapping[str, Glyph],
    text: str,
    *,
    use_join_advance: bool = True,
) -> tuple[list[JoinPairMeasure], float]:
    """Adjacent non-space pairs in ``text`` → measures + gap CV.

    When ``use_join_advance`` and both anchors exist, advance is join-derived;
    otherwise the left glyph's stored advance is used (gappy sans-serif case).
    """
    from typekernel.font.glyph import glyph_name_for_char

    names: list[str] = []
    for ch in text:
        if ch.isspace():
            continue
        try:
            gn = glyph_name_for_char(ch)
        except ValueError:
            continue
        if gn in glyphs:
            names.append(gn)
    measures: list[JoinPairMeasure] = []
    for i in range(len(names) - 1):
        left = glyphs[names[i]]
        right = glyphs[names[i + 1]]
        adv: float | None = None
        if use_join_advance:
            ex = anchor_by_name(left, EXIT)
            en = anchor_by_name(right, ENTRY)
            if ex is not None and en is not None:
                adv = join_advance(ex, en)
        measures.append(measure_join_pair(left, right, advance=adv))
    gaps = [m.gap for m in measures if m.has_join] or [m.gap for m in measures]
    return measures, gap_cv(gaps)

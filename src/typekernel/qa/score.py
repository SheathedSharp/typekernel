"""Quantitative specimen scores for words (bbox vs optical, stems, joins).

Cubic outlines remain the design truth; these numbers exist so agents can tell
whether spacing got *optically* even — bounding-box gaps alone are not enough.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from typekernel.geo.joins import classify_joins, curvature_jump
from typekernel.geo.layout import union_bounds
from typekernel.geo.outline import Outline
from typekernel.geo.smoothness import is_g1_join
from typekernel.optics.space import (
    OpticalSpacingResult,
    pair_gap_bbox,
    pair_gap_optical,
    space_word_optical,
)
from typekernel.optics.stem import measure_vertical_stem
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext
from typekernel.parts.latin import word_zayju
from typekernel.parts.metrics import KernTable, default_sans_kern, layout_glyphs

GapMode = Literal["bbox", "optical"]


@dataclass(frozen=True, slots=True)
class Score:
    """One scalar metric with optional detail payload."""

    name: str
    value: float
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WordReport:
    """Full word specimen scorecard."""

    text: str
    bbox_gaps: tuple[float, ...]
    optical_gaps: tuple[float, ...]
    bbox_gap_spread: float
    optical_gap_spread: float
    bbox_gap_ratio: float
    optical_gap_ratio: float
    stem_widths: tuple[float, ...]
    stem_cv: float
    g1_join_error_count: int
    g1_join_total: int
    kink_count: int = 0
    corner_count: int = 0
    terminal_count: int = 0
    curvature_jump: float = 0.0
    target_gap: float | None = None
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write_json(self, path: Path | str) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return out


def _gap_spread(gaps: list[float]) -> float:
    if not gaps:
        return 0.0
    return max(gaps) - min(gaps)


def _gap_ratio(gaps: list[float]) -> float:
    """max/min; 1.0 is perfectly even. Empty → 1.0; non-positive min → inf."""
    if not gaps:
        return 1.0
    lo = min(gaps)
    hi = max(gaps)
    if lo <= 1e-9:
        return float("inf") if hi > 0 else 1.0
    return hi / lo


def _kern_between(table: KernTable | None, a: str, b: str) -> float:
    if table is None:
        return 0.0
    return table.lookup(a, b)


def word_gap_spread(
    glyphs: list[ComposedGlyph],
    names: list[str],
    *,
    mode: GapMode = "optical",
    kerning: KernTable | None = None,
    samples: int = 17,
) -> Score:
    """Spread (max−min) of consecutive letter gaps in ``mode``."""
    if len(glyphs) != len(names):
        raise ValueError("names length must match glyphs")
    gaps: list[float] = []
    for i in range(len(glyphs) - 1):
        k = _kern_between(kerning, names[i], names[i + 1])
        if mode == "bbox":
            gaps.append(pair_gap_bbox(glyphs[i], glyphs[i + 1], kern=k))
        else:
            gaps.append(
                pair_gap_optical(glyphs[i], glyphs[i + 1], kern=k, samples=samples)
            )
    spread = _gap_spread(gaps)
    return Score(
        name=f"gap_spread_{mode}",
        value=spread,
        detail={
            "gaps": gaps,
            "ratio": _gap_ratio(gaps),
            "mean": (sum(gaps) / len(gaps)) if gaps else 0.0,
        },
    )


def _stem_probes_for_glyph(glyph: ComposedGlyph) -> list[float]:
    """Probe x positions likely to hit vertical stems (ink bbox thirds + mid)."""
    ink = list(glyph.solids) + list(glyph.holes)
    try:
        min_x, _, max_x, _ = union_bounds(ink)
    except ValueError:
        return []
    w = max_x - min_x
    if w <= 1.0:
        return [(min_x + max_x) / 2.0]
    return [
        min_x + w * 0.15,
        min_x + w * 0.35,
        min_x + w * 0.50,
        min_x + w * 0.65,
        min_x + w * 0.85,
    ]


def stem_uniformity(
    glyphs: list[ComposedGlyph],
    *,
    probes: list[float] | None = None,
    expected_stem: float | None = None,
    tolerance: float = 0.20,
) -> Score:
    """Coefficient of variation of vertical stems near ``expected_stem``.

    Probes that hit counters, crotches, or diagonals are dropped when
    ``expected_stem`` is set (default: each glyph's ``context.stem``): keep
    widths within ``±tolerance`` fraction of that target so the CV reflects
    stem colour, not silhouette accidents.
    """
    widths: list[float] = []
    raw: list[float] = []
    for glyph in glyphs:
        target = glyph.context.stem if expected_stem is None else expected_stem
        lo, hi = target * (1.0 - tolerance), target * (1.0 + tolerance)
        xs = probes if probes is not None else _stem_probes_for_glyph(glyph)
        for outline in glyph.solids:
            for x in xs:
                w = measure_vertical_stem(outline, x)
                if w is None or w <= 1.0:
                    continue
                raw.append(w)
                if lo <= w <= hi:
                    widths.append(w)
    if len(widths) < 2:
        return Score(
            "stem_cv",
            0.0,
            {"widths": widths, "raw_widths": raw, "n": len(widths)},
        )
    mean = sum(widths) / len(widths)
    var = sum((w - mean) ** 2 for w in widths) / len(widths)
    cv = math.sqrt(var) / mean if mean > 1e-9 else 0.0
    return Score(
        "stem_cv",
        cv,
        {"widths": widths, "raw_widths": raw, "mean": mean, "n": len(widths)},
    )


def join_smoothness(outline: Outline, *, tol: float = 1e-3) -> Score:
    """Count non-G1 joins across closed contours."""
    bad = 0
    total = 0
    for contour in outline.contours:
        segs = contour.segments
        n = len(segs)
        if n < 2:
            continue
        for i in range(n):
            total += 1
            a = segs[i]
            b = segs[(i + 1) % n]
            if not is_g1_join(a, b, tol=tol):
                bad += 1
    return Score(
        "g1_join_errors",
        float(bad),
        {"error_count": bad, "join_total": total, "tol": tol},
    )


def join_smoothness_glyph(glyph: ComposedGlyph, *, tol: float = 1e-3) -> Score:
    bad = 0
    total = 0
    for outline in list(glyph.solids) + list(glyph.holes):
        s = join_smoothness(outline, tol=tol)
        bad += int(s.detail["error_count"])
        total += int(s.detail["join_total"])
    return Score(
        "g1_join_errors",
        float(bad),
        {"error_count": bad, "join_total": total, "tol": tol},
    )


def word_report(
    glyphs: list[ComposedGlyph],
    names: list[str],
    *,
    kerning: KernTable | None = None,
    samples: int = 17,
    target_gap: float | None = None,
    notes: tuple[str, ...] = (),
) -> WordReport:
    """Score a word: bbox + optical gaps, stem CV, G1 join errors."""
    if len(glyphs) != len(names):
        raise ValueError("names length must match glyphs")
    bbox = word_gap_spread(glyphs, names, mode="bbox", kerning=kerning, samples=samples)
    optical = word_gap_spread(
        glyphs, names, mode="optical", kerning=kerning, samples=samples
    )
    stems = stem_uniformity(glyphs)
    g1_bad = 0
    g1_total = 0
    kinks = corners = terminals = 0
    jump = 0.0
    for g in glyphs:
        s = join_smoothness_glyph(g)
        g1_bad += int(s.detail["error_count"])
        g1_total += int(s.detail["join_total"])
        for o in list(g.solids) + list(g.holes):
            jc = classify_joins(o)
            kinks += jc.kinks
            corners += jc.corners
            terminals += jc.terminals
            jump = max(jump, curvature_jump(o))
    return WordReport(
        text="".join(names),
        bbox_gaps=tuple(float(x) for x in bbox.detail["gaps"]),
        optical_gaps=tuple(float(x) for x in optical.detail["gaps"]),
        bbox_gap_spread=float(bbox.value),
        optical_gap_spread=float(optical.value),
        bbox_gap_ratio=float(bbox.detail["ratio"]),
        optical_gap_ratio=float(optical.detail["ratio"]),
        stem_widths=tuple(float(x) for x in stems.detail.get("widths", [])),
        stem_cv=float(stems.value),
        g1_join_error_count=g1_bad,
        g1_join_total=g1_total,
        kink_count=kinks,
        corner_count=corners,
        terminal_count=terminals,
        curvature_jump=jump,
        target_gap=target_gap,
        notes=notes,
    )


def zayju_report(
    ctx: DesignContext | None = None,
    *,
    optical: bool = True,
    samples: int = 17,
) -> tuple[WordReport, list[ComposedGlyph], KernTable]:
    """Build ``zayju``, optionally optically re-space, and return a report.

    Returns ``(report, glyphs, kerning)`` so callers can render the same layout
    that was scored.
    """
    ctx = ctx or DesignContext.geometric_sans()
    names = list("zayju")
    base = word_zayju(ctx)
    if optical:
        result: OpticalSpacingResult = space_word_optical(base, names, samples=samples)
        glyphs = list(result.glyphs)
        kerning = result.kerning
        note = ("optical_spacing",)
        target = result.target_gap
    else:
        glyphs = base
        kerning = default_sans_kern()
        note = ("heuristic_spacing",)
        target = None
    report = word_report(
        glyphs,
        names,
        kerning=kerning,
        samples=samples,
        target_gap=target,
        notes=note,
    )
    return report, glyphs, kerning


def layout_xs(
    glyphs: list[ComposedGlyph],
    names: list[str],
    kerning: KernTable | None,
) -> list[float]:
    """Pen-x positions matching :func:`word_report` layout."""
    return layout_glyphs(glyphs, names, kerning=kerning)

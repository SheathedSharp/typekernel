"""Topology measures on a live outline (target §7.4).

After ``pathops.simplify`` (nonzero), outer contours are ink islands and holes
are counters. Slit counters (area < ``slit_factor * stem²``) are reported
separately so diagnose can warn without counting them as real counters.
"""

from __future__ import annotations

from dataclasses import dataclass

from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.perceive.render import simplify_outline

__all__ = ["Topology", "contour_signed_area", "measure_topology"]


def contour_signed_area(points: list[Point]) -> float:
    """Shoelace area; positive ≈ CCW (font ink convention after fix_winding)."""
    if len(points) < 3:
        return 0.0
    acc = 0.0
    n = len(points)
    for i in range(n):
        x1, y1 = points[i].x, points[i].y
        x2, y2 = points[(i + 1) % n].x, points[(i + 1) % n].y
        acc += x1 * y2 - x2 * y1
    return acc * 0.5


def _on_curve_points(outline: Outline) -> list[list[Point]]:
    out: list[list[Point]] = []
    for contour in outline.contours:
        if not contour.segments:
            continue
        pts: list[Point] = []
        for segment in contour.segments:
            start = segment.points[0]
            if not pts or pts[-1] != start:
                pts.append(start)
            end = segment.points[-1]
            if pts[-1] != end:
                pts.append(end)
        if len(pts) >= 2 and pts[0] == pts[-1]:
            pts = pts[:-1]
        out.append(pts)
    return out


@dataclass(frozen=True, slots=True)
class Topology:
    """Measured counters / islands after nonzero simplify."""

    counters: int
    islands: int
    slit_counters: int
    counter_areas: tuple[float, ...]
    island_areas: tuple[float, ...]
    simplified: Outline


def measure_topology(
    outline: Outline,
    *,
    stem: float = 80.0,
    slit_factor: float = 0.25,
) -> Topology:
    """Count ink islands and counters on ``outline``.

    ``slit_factor * stem²`` is the area below which a hole is a slit (overlap
    join artefact), not a real counter.
    """
    simplified = simplify_outline(outline)
    slit_thresh = max(1.0, float(slit_factor) * float(stem) * float(stem))
    island_areas: list[float] = []
    counter_areas: list[float] = []
    slits = 0
    for pts in _on_curve_points(simplified):
        area = contour_signed_area(pts)
        abs_area = abs(area)
        if abs_area < 1e-6:
            continue
        if area > 0:
            island_areas.append(abs_area)
        elif abs_area < slit_thresh:
            slits += 1
        else:
            counter_areas.append(abs_area)
    return Topology(
        counters=len(counter_areas),
        islands=len(island_areas),
        slit_counters=slits,
        counter_areas=tuple(counter_areas),
        island_areas=tuple(island_areas),
        simplified=simplified,
    )

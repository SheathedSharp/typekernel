"""Structural lint for composed glyphs (design truth, not PNG aesthetics)."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from typing import Any, Literal

from typekernel.geo.contour import signed_area
from typekernel.geo.extrema import cubic_has_off_node_axis_extrema
from typekernel.geo.layout import union_bounds
from typekernel.geo.outline import Outline
from typekernel.geo.pens import draw_outline
from typekernel.geo.segment import CubicSegment
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext
from typekernel.parts.family import Controls

Severity = Literal["error", "warn"]

__all__ = [
    "LintIssue",
    "LintReport",
    "lint_controls",
    "lint_glyph",
]


@dataclass(frozen=True, slots=True)
class LintIssue:
    glyph: str
    rule: str
    severity: Severity
    detail: str


@dataclass(frozen=True, slots=True)
class LintReport:
    issues: tuple[LintIssue, ...]

    @property
    def errors(self) -> tuple[LintIssue, ...]:
        return tuple(i for i in self.issues if i.severity == "error")

    def ok(self) -> bool:
        return not self.errors


def _has_pathops() -> bool:
    return bool(importlib.util.find_spec("pathops"))


def _outline_to_path(outline: Outline) -> Any:
    import pathops

    path = pathops.Path()
    draw_outline(outline, path.getPen())
    return path


def _contour_keyhole(contour_outline: Outline) -> bool:
    if not _has_pathops():
        return False
    import pathops

    path = _outline_to_path(contour_outline)
    n_before = len(list(path.contours))
    if n_before != 1:
        return False
    simplified = pathops.Path(path)
    simplified.simplify(fix_winding=True)
    n_after = len(list(simplified.contours))
    return n_after != n_before


def _path_self_intersects(outline: Outline) -> bool:
    if not _has_pathops():
        return False
    import pathops

    path = _outline_to_path(outline)
    simplified = pathops.Path(path)
    simplified.simplify(fix_winding=True)
    # If simplify reduces area vs union of parts, likely self-crossing (heuristic).
    from fontTools.pens.areaPen import AreaPen

    pen_a = AreaPen()
    path.draw(pen_a)
    pen_b = AreaPen()
    simplified.draw(pen_b)
    delta = abs(abs(pen_a.value) - abs(pen_b.value))
    return bool(delta > 0.01 * max(abs(pen_a.value), 1.0))


def _degenerate_contour(outline: Outline) -> bool:
    for contour in outline.contours:
        if not contour.segments:
            return True
        if len(contour.segments) < 2 and contour.closed:
            return True
    return False


def lint_glyph(
    glyph: ComposedGlyph,
    ctx: DesignContext,
    *,
    glyph_name: str = "?",
    control_max_thickness_ratio: float | None = None,
    counter_gap_floor: float | None = None,
) -> tuple[LintIssue, ...]:
    """Run structural rules on one :class:`~typekernel.parts.compose.ComposedGlyph`."""
    issues: list[LintIssue] = []

    for label, parts in (("solid", glyph.solids), ("hole", glyph.holes)):
        for outline in parts:
            if _degenerate_contour(outline):
                issues.append(
                    LintIssue(glyph_name, "R6_degenerate", "error", f"{label} has empty contour")
                )
            contours = outline.contours
            if label == "solid":
                closed = [c for c in contours if c.closed]
                if len(closed) == 1 and signed_area(closed[0]) < 0:
                    issues.append(
                        LintIssue(
                            glyph_name,
                            "R1_winding",
                            "error",
                            f"{label} contour has negative signed area",
                        )
                    )
                elif len(closed) > 1 and not any(signed_area(c) > 0 for c in closed):
                    issues.append(
                        LintIssue(
                            glyph_name,
                            "R1_winding",
                            "error",
                            "solid outline has no counter-clockwise outer contour",
                        )
                    )
            for contour in contours:
                piece = Outline((contour,))
                area = signed_area(contour)
                if label == "hole" and contour.closed and area > 0:
                    issues.append(
                        LintIssue(
                            glyph_name,
                            "R1_winding",
                            "error",
                            f"{label} contour should be clockwise (negative area)",
                        )
                    )
                if _contour_keyhole(piece):
                    issues.append(
                        LintIssue(
                            glyph_name,
                            "R2_keyhole",
                            "warn",
                            f"{label} contour has zero-width seam (keyhole)",
                        )
                    )
            if _path_self_intersects(outline):
                issues.append(
                    LintIssue(
                        glyph_name,
                        "R3_self_intersect",
                        "error",
                        f"{label} outline self-intersection or overlap",
                    )
                )
            off_node = any(
                isinstance(seg, CubicSegment) and cubic_has_off_node_axis_extrema(seg)
                for contour in contours
                for seg in contour.segments
            )
            if off_node:
                issues.append(
                    LintIssue(
                        glyph_name,
                        "R4_extrema",
                        "warn",
                        f"{label} cubic has axis extremum away from on-curve nodes",
                    )
                )

    ink = list(glyph.solids) + list(glyph.holes)
    if ink:
        x0, y0, x1, y1 = union_bounds(ink)
        if x0 < -1.0:
            issues.append(
                LintIssue(
                    glyph_name,
                    "R7_sidebearing",
                    "error",
                    f"ink extends left of origin (x0={x0:.1f})",
                )
            )
        if x1 > glyph.advance + 1.0:
            issues.append(
                LintIssue(
                    glyph_name,
                    "R7_sidebearing",
                    "error",
                    f"ink extends past advance (x1={x1:.1f} > {glyph.advance:.1f})",
                )
            )
        overshoot = ctx.overshoot
        if y1 > ctx.ascender + overshoot + ctx.cap_height * 0.05:
            issues.append(
                LintIssue(
                    glyph_name,
                    "R5_zones",
                    "warn",
                    f"top y={y1:.0f} far above ascender zone",
                )
            )
        if y0 < ctx.descender - overshoot - abs(ctx.descender) * 0.15:
            issues.append(
                LintIssue(
                    glyph_name,
                    "R5_zones",
                    "warn",
                    f"bottom y={y0:.0f} far below descender zone",
                )
            )

    if control_max_thickness_ratio is not None:
        from typekernel.qa.thickness import (
            LINT_THICKNESS_GRID,
            THICKNESS_OUTLIER_FACTOR,
            thickness_ratio_to_stem,
        )

        ratio = thickness_ratio_to_stem(glyph, ctx.stem, grid=LINT_THICKNESS_GRID)
        limit = control_max_thickness_ratio * THICKNESS_OUTLIER_FACTOR
        if ratio > limit:
            issues.append(
                LintIssue(
                    glyph_name,
                    "R9_thickness_outlier",
                    "warn",
                    f"max/stem {ratio:.2f} exceeds control band {limit:.2f}",
                )
            )

    if counter_gap_floor is not None and counter_gap_floor > 0:
        from typekernel.qa.counter import min_counter_gap

        gap = min_counter_gap(glyph)
        if gap < counter_gap_floor:
            issues.append(
                LintIssue(
                    glyph_name,
                    "R8_counter_min",
                    "error",
                    f"counter pinch {gap:.1f} below floor {counter_gap_floor:.1f}",
                )
            )

    return tuple(issues)


def lint_controls(
    controls: Controls,
    chars: str | None = None,
    *,
    thickness: bool = False,
    counter_min: bool = False,
) -> LintReport:
    """Lint every glyph from ``controls.build_all(chars)``."""
    charset = chars if chars is not None else controls.supported
    drawn = controls.build_all(charset)
    ctx = controls.context
    control_ratio: float | None = None
    if thickness:
        from typekernel.qa.thickness import control_max_thickness_ratio

        control_ratio = control_max_thickness_ratio(controls)
    gap_floor: float | None = None
    if counter_min:
        from typekernel.parts.weight_relief import counter_gap_floor

        gap_floor = counter_gap_floor(ctx.stem)
    all_issues: list[LintIssue] = []
    for ch in charset:
        if ch not in drawn:
            all_issues.append(
                LintIssue(ch, "R0_missing", "error", "glyph not built")
            )
            continue
        from typekernel.qa.counter import COUNTER_PINCH_CHARSET

        floor = gap_floor if counter_min and ch in COUNTER_PINCH_CHARSET else None
        all_issues.extend(
            lint_glyph(
                drawn[ch],
                ctx,
                glyph_name=ch,
                control_max_thickness_ratio=control_ratio,
                counter_gap_floor=floor,
            )
        )
    return LintReport(tuple(all_issues))

"""Rule-based glyph identity checks (topology and zones, not bitmap matching)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from typekernel.geo.contour import signed_area
from typekernel.geo.layout import union_bounds
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext
from typekernel.parts.family import FormSources

Severity = Literal["error", "warn"]

__all__ = [
    "IdentityExpectation",
    "IdentityIssue",
    "IdentityReport",
    "check_identity_controls",
    "check_identity_glyph",
]

Checker = Callable[[ComposedGlyph, DesignContext], str | None]


@dataclass(frozen=True, slots=True)
class IdentityExpectation:
    """Declarative expectations for one codepoint."""

    min_holes: int = 0
    max_holes: int | None = None
    min_solids: int = 1
    min_ink_top: float | None = None
    """Lowest acceptable top ink y (design units)."""
    max_ink_top: float | None = None
    checker: str | None = None


@dataclass(frozen=True, slots=True)
class IdentityIssue:
    glyph: str
    rule: str
    severity: Severity
    detail: str


@dataclass(frozen=True, slots=True)
class IdentityReport:
    issues: tuple[IdentityIssue, ...]

    @property
    def errors(self) -> tuple[IdentityIssue, ...]:
        return tuple(i for i in self.issues if i.severity == "error")

    def ok(self) -> bool:
        return not self.errors


def _hole_contour_count(glyph: ComposedGlyph) -> int:
    count = sum(len(o.contours) for o in glyph.holes)
    for solid in glyph.solids:
        count += sum(1 for c in solid.contours if signed_area(c) < 0)
    return count


def _solid_part_count(glyph: ComposedGlyph) -> int:
    return len(glyph.solids)


def _ink_bounds(glyph: ComposedGlyph) -> tuple[float, float, float, float]:
    ink = list(glyph.solids) + list(glyph.holes)
    if not ink:
        return (0.0, 0.0, 0.0, 0.0)
    return union_bounds(ink)


def _solid_centroids(glyph: ComposedGlyph) -> list[tuple[float, float, float, float]]:
    """(cx, cy, width, height) per solid outline bounds."""
    out: list[tuple[float, float, float, float]] = []
    for solid in glyph.solids:
        x0, y0, x1, y1 = union_bounds([solid])
        out.append(((x0 + x1) / 2.0, (y0 + y1) / 2.0, x1 - x0, y1 - y0))
    return out


def _check_exclam_dot_low(glyph: ComposedGlyph, ctx: DesignContext) -> str | None:
    """Exclamation dot should sit low (near baseline), not above the stem."""
    parts = _solid_centroids(glyph)
    if not parts:
        return None
    top = max(parts, key=lambda t: t[1])
    if top[1] > ctx.x_height * 0.62 and top[3] < ctx.stem * 1.25:
        return "dot reads above stem (should be near baseline)"
    return None


def _check_question_tail(glyph: ComposedGlyph, ctx: DesignContext) -> str | None:
    xh = ctx.x_height
    parts = _solid_centroids(glyph)
    stem_like = [
        p
        for p in parts
        if p[2] <= ctx.stem * 1.2 and p[3] >= xh * 0.08 and p[1] < xh * 0.52
    ]
    if not stem_like:
        return "missing descender stem below bowl"
    return None


def _check_ampersand_not_e(glyph: ComposedGlyph, ctx: DesignContext) -> str | None:
    _, _, _, y1 = _ink_bounds(glyph)
    if y1 < ctx.cap_height * 0.82:
        return "ink does not reach cap zone (reads like lowercase e)"
    holes = _hole_contour_count(glyph)
    if holes < 1:
        return "expected counter aperture for ampersand"
    return None


def _check_hash_not_plus(glyph: ComposedGlyph, ctx: DesignContext) -> str | None:
    if _solid_part_count(glyph) != 1:
        return None
    x0, y0, x1, y1 = _ink_bounds(glyph)
    w, h = x1 - x0, y1 - y0
    if w < 1 or h < 1:
        return None
    aspect = w / h
    if 0.85 < aspect < 1.18 and _hole_contour_count(glyph) == 0:
        return "hash is a single plus-like blob (need two bars)"
    return None


def _check_dollar_loops(glyph: ComposedGlyph, ctx: DesignContext) -> str | None:
    if not glyph.solids:
        return "expected dollar sign ink"
    if _hole_contour_count(glyph) < 2:
        return "dollar loops lack counters (need ring forms)"
    return None


def _check_percent_rings(glyph: ComposedGlyph, ctx: DesignContext) -> str | None:
    if not glyph.solids:
        return "expected percent sign ink"
    if _hole_contour_count(glyph) < 2:
        return "percent rings lack counters (need ring forms)"
    return None


_CHECKERS: dict[str, Checker] = {
    "exclam_dot_low": _check_exclam_dot_low,
    "question_tail": _check_question_tail,
    "ampersand_not_e": _check_ampersand_not_e,
    "hash_not_plus": _check_hash_not_plus,
    "dollar_loops": _check_dollar_loops,
    "percent_rings": _check_percent_rings,
}


def _expectations_for(ctx: DesignContext) -> dict[str, IdentityExpectation]:
    cap = ctx.cap_height
    xh = ctx.x_height
    return {
        "!": IdentityExpectation(checker="exclam_dot_low"),
        "?": IdentityExpectation(checker="question_tail"),
        "&": IdentityExpectation(min_ink_top=cap * 0.82, checker="ampersand_not_e"),
        "#": IdentityExpectation(checker="hash_not_plus"),
        "$": IdentityExpectation(checker="dollar_loops"),
        "%": IdentityExpectation(checker="percent_rings"),
        "i": IdentityExpectation(min_solids=2),
        "j": IdentityExpectation(min_solids=2),
        "o": IdentityExpectation(min_holes=1),
        "O": IdentityExpectation(min_holes=1),
        "0": IdentityExpectation(min_holes=1),
        "8": IdentityExpectation(min_holes=1),
        "a": IdentityExpectation(min_holes=1),
        "e": IdentityExpectation(min_holes=1),
        "b": IdentityExpectation(min_holes=1),
        "d": IdentityExpectation(min_holes=1),
        "p": IdentityExpectation(min_holes=1),
        "q": IdentityExpectation(min_holes=1),
        "g": IdentityExpectation(min_holes=1),
        "A": IdentityExpectation(min_ink_top=xh * 0.95),
        "H": IdentityExpectation(min_ink_top=cap * 0.92),
    }


def check_identity_glyph(
    glyph: ComposedGlyph,
    ctx: DesignContext,
    *,
    glyph_name: str,
    expectation: IdentityExpectation | None = None,
) -> tuple[IdentityIssue, ...]:
    exp = expectation or _expectations_for(ctx).get(glyph_name)
    if exp is None:
        return ()
    issues: list[IdentityIssue] = []
    holes = _hole_contour_count(glyph)
    solids = _solid_part_count(glyph)
    if holes < exp.min_holes:
        issues.append(
            IdentityIssue(
                glyph_name,
                "holes",
                "error",
                f"hole count {holes} < min {exp.min_holes}",
            )
        )
    if exp.max_holes is not None and holes > exp.max_holes:
        issues.append(
            IdentityIssue(
                glyph_name,
                "holes",
                "error",
                f"hole count {holes} > max {exp.max_holes}",
            )
        )
    if solids < exp.min_solids:
        issues.append(
            IdentityIssue(
                glyph_name,
                "solids",
                "error",
                f"solid parts {solids} < min {exp.min_solids}",
            )
        )
    _, _, _, y1 = _ink_bounds(glyph)
    if exp.min_ink_top is not None and y1 < exp.min_ink_top:
        issues.append(
            IdentityIssue(
                glyph_name,
                "zone_top",
                "error",
                f"top ink {y1:.1f} below minimum {exp.min_ink_top:.1f}",
            )
        )
    if exp.max_ink_top is not None and y1 > exp.max_ink_top:
        issues.append(
            IdentityIssue(
                glyph_name,
                "zone_top",
                "error",
                f"top ink {y1:.1f} above maximum {exp.max_ink_top:.1f}",
            )
        )
    if exp.checker:
        fn = _CHECKERS.get(exp.checker)
        if fn is not None:
            msg = fn(glyph, ctx)
            if msg:
                issues.append(
                    IdentityIssue(glyph_name, exp.checker, "error", msg)
                )
    return tuple(issues)


def check_identity_controls(
    controls: FormSources,
    chars: str | None = None,
) -> IdentityReport:
    charset = chars if chars is not None else controls.supported
    ctx = controls.context
    expectations = _expectations_for(ctx)
    drawn = controls.derive(charset)
    all_issues: list[IdentityIssue] = []
    for ch in charset:
        if ch not in drawn:
            all_issues.append(IdentityIssue(ch, "missing", "error", "glyph not built"))
            continue
        exp = expectations.get(ch)
        if exp is None:
            continue
        all_issues.extend(
            check_identity_glyph(
                drawn[ch],
                ctx,
                glyph_name=ch,
                expectation=exp,
            )
        )
    return IdentityReport(tuple(all_issues))

"""Adjacent / sequential glyph style consistency (designer-order gate).

Human type design proceeds **one glyph at a time**, checking the new letter
against control and previously unlocked letters. A brief phrase is a late
specimen — not the design method.

This module works on abstract :class:`~typekernel.parts.compose.ComposedGlyph`
outlines (Controls-derived **or** skeleton / ``trace_letter`` faces).
"""

from __future__ import annotations

import math
import statistics
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from typekernel.geo.outline import Outline, bounds
from typekernel.optics.stem import list_horizontal_stems, list_vertical_stems
from typekernel.parts.compose import ComposedGlyph

# Optics ↔ QA: diagonal stem remap uses optics.stem.vertical_equiv_from_diagonal
# (inverse of diagonal_compensation). Further shared stem helpers: only if a
# second call site appears; avoid sprawling rewrite.

__all__ = [
    "GlyphStyleMetrics",
    "SequenceStyleReport",
    "StyleCheck",
    "StyleConsistencyReport",
    "StyleConsistencyTolerances",
    "check_design_sequence",
    "compare_glyph_styles",
    "extract_glyph_style_metrics",
    "fix_hint_for_check",
    "script_body_tolerances",
]


def _ink_outline(glyph: ComposedGlyph) -> Outline:
    if not glyph.solids:
        raise ValueError("glyph has no solid outlines")
    if len(glyph.solids) == 1:
        return glyph.solids[0]
    from typekernel.geo.boolean import union_all

    try:
        return union_all(list(glyph.solids))
    except (RuntimeError, ValueError, TypeError):
        return glyph.solids[0]


def _sample_oncurve_points(outline: Outline) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for contour in outline.contours:
        for seg in contour.segments:
            p0 = seg.points[0]
            p1 = seg.points[-1]
            if not pts or pts[-1] != (p0.x, p0.y):
                pts.append((float(p0.x), float(p0.y)))
            pts.append((float(p1.x), float(p1.y)))
    return pts


def _band_rail_y(
    pts: Sequence[tuple[float, float]],
    *,
    x0: float,
    x1: float,
) -> float | None:
    """Mean Y of the lowest quartile of points in an x-band (entry/exit rails)."""
    band = [p[1] for p in pts if x0 <= p[0] <= x1]
    if len(band) < 2:
        return float(band[0]) if band else None
    band = sorted(band)
    n = max(1, len(band) // 4)
    return float(statistics.fmean(band[:n]))


def _exit_slant_deg(
    pts: Sequence[tuple[float, float]],
    *,
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
) -> float | None:
    """Rough stroke angle (degrees from +x) in the lower-right exit region."""
    w = xmax - xmin
    h = ymax - ymin
    if w < 1.0 or h < 1.0:
        return None
    region = [
        p
        for p in pts
        if p[0] >= xmax - 0.22 * w and p[1] <= ymin + 0.45 * h
    ]
    if len(region) < 3:
        region = [p for p in pts if p[0] >= xmax - 0.18 * w]
    if len(region) < 3:
        return None
    region = sorted(region, key=lambda p: p[0])
    x0, y0 = region[0]
    x1, y1 = region[-1]
    dx, dy = x1 - x0, y1 - y0
    if abs(dx) < 1e-6 and abs(dy) < 1e-6:
        return None
    return math.degrees(math.atan2(dy, dx))



_HINT_DIRECTION: dict[str, tuple[str, str]] = {
    # metric → (when cand > ref, when cand < ref)
    "stem_median": (
        "reduce candidate stem thickness toward the reference",
        "increase candidate stem thickness toward the reference",
    ),
    "oriented_stem": (
        "reduce candidate diagonal / oriented stem thickness toward the reference",
        "increase candidate diagonal / oriented stem thickness toward the reference",
    ),
    "contrast_ratio": (
        "even candidate stroke contrast (less H/V disparity) toward the reference",
        "increase candidate stroke contrast toward the reference",
    ),
    "entry_rail_y": (
        "lower candidate entry / lead-in rail toward the reference Y",
        "raise candidate entry / lead-in rail toward the reference Y",
    ),
    "exit_rail_y": (
        "lower candidate exit / trail rail toward the reference Y",
        "raise candidate exit / trail rail toward the reference Y",
    ),
    "exit_slant_deg": (
        "rotate candidate exit flatter / more clockwise toward the reference slant",
        "rotate candidate exit steeper / more counter-clockwise toward the reference slant",
    ),
    "bowl_center_y": (
        "shift candidate bowl / body centre downward toward the reference",
        "shift candidate bowl / body centre upward toward the reference",
    ),
    "ink_ymin": (
        "raise candidate lowest ink (less deep descender / overshoot) toward the reference",
        "lower candidate lowest ink toward the reference",
    ),
    "ink_ymax": (
        "lower candidate highest ink (shorter ascender / less overshoot) toward the reference",
        "raise candidate highest ink toward the reference",
    ),
}


def fix_hint_for_check(
    name: str,
    reference: float | None,
    candidate: float | None,
    *,
    ok: bool,
) -> str:
    """Actionable one-line hint for an agent redesigning the candidate glyph."""
    if ok:
        return ""
    if reference is None or candidate is None:
        return f"{name}: measurement missing — ensure the outline has sampleable ink"
    pair = _HINT_DIRECTION.get(name)
    if pair is None:
        return f"{name}: move candidate ({candidate:.1f}) toward reference ({reference:.1f})"
    hi, lo = pair
    direction = hi if candidate > reference else lo
    return (
        f"{name}: candidate={candidate:.1f} reference={reference:.1f} "
        f"(delta={abs(candidate - reference):.1f}) — {direction}"
    )


@dataclass(frozen=True, slots=True)
class GlyphStyleMetrics:
    """Measurable style proxies for one designed outline."""

    stem_median: float | None
    contrast_ratio: float | None
    ink_ymin: float
    ink_ymax: float
    ink_xmin: float
    ink_xmax: float
    entry_rail_y: float | None
    """Mean Y of lower-left ink (entry / lead-in band)."""
    exit_rail_y: float | None
    """Mean Y of lower-right ink (exit / trail band)."""
    exit_slant_deg: float | None
    bowl_center_y: float
    """Vertical centre of ink bounds (bowl / body alignment proxy)."""
    oriented_stem: float | None = None
    """Median perpendicular thickness from oriented probes (diagonals)."""


@dataclass(frozen=True, slots=True)
class StyleConsistencyTolerances:
    """Absolute deltas (design units / degrees / ratio) allowed between glyphs.

    ``ink_ymax`` defaults wide so ascenders/descenders can be gated on rails and
    stems against a body control without failing on height alone. Tighten it when
    comparing same-role letters (e.g. ``a`` vs ``e``).

    ``stem_median_rel`` (when > 0) raises the stem limit to
    ``max(stem_median, stem_median_rel * |reference|)`` so black masters with
    designed bowl thickening stay gated without an absolute floor that only
    fits Regular.
    """

    stem_median: float = 12.0
    stem_median_rel: float = 0.0
    contrast_ratio: float = 0.35
    entry_rail_y: float = 36.0
    exit_rail_y: float = 36.0
    exit_slant_deg: float = 35.0
    bowl_center_y: float = 55.0
    ink_ymin: float = 55.0
    ink_ymax: float = 400.0


def script_body_tolerances() -> StyleConsistencyTolerances:
    """Tighter budgets for same-role script letters (no ascender/descender jump)."""
    return StyleConsistencyTolerances(
        stem_median=12.0,
        contrast_ratio=0.32,
        entry_rail_y=32.0,
        exit_rail_y=32.0,
        exit_slant_deg=32.0,
        bowl_center_y=48.0,
        ink_ymin=55.0,
        ink_ymax=100.0,
    )


@dataclass(frozen=True, slots=True)
class StyleCheck:
    """One named metric comparison."""

    name: str
    reference: float | None
    candidate: float | None
    delta: float | None
    limit: float
    ok: bool
    note: str = ""
    hint: str = ""
    """Empty when ok; otherwise an actionable redesign direction."""


@dataclass(frozen=True, slots=True)
class StyleConsistencyReport:
    """Pass/fail report comparing a candidate glyph to a reference."""

    reference_name: str
    candidate_name: str
    checks: tuple[StyleCheck, ...]
    passed: bool
    reference: GlyphStyleMetrics
    candidate: GlyphStyleMetrics

    @property
    def failures(self) -> tuple[StyleCheck, ...]:
        return tuple(c for c in self.checks if not c.ok)

    def fix_hints(self) -> tuple[str, ...]:
        """Actionable redesign lines for every failing check."""
        return tuple(
            c.hint or fix_hint_for_check(c.name, c.reference, c.candidate, ok=False)
            for c in self.failures
        )



def _body_stem_median(outline: Outline) -> float | None:
    """Median vertical-stem width in a body-safe Y band.

    Mid-bounds probes on ascenders hit the shoulder join (false thick ``h``).
    Multi-stem / bowl letters use a mid-height band; single tall stems stay in
    the lower body. Spans wider than ``0.42×ink`` (counters, ``e`` crossbars,
    full bowl chords) are dropped. Narrow letters whose stem ≈ ink width fall
    back to an uncapped sample clustered around the *narrowest* upright.
    """
    try:
        xmin, ymin, xmax, ymax = bounds(outline)
    except ValueError:
        return None
    h = max(ymax - ymin, 1.0)
    wmax = max(xmax - xmin, 1.0)
    frac_cap = 0.42 * wmax
    mid_y = ymin + 0.45 * h
    mid_capped = list_vertical_stems(outline, y=mid_y, max_width=frac_cap)
    mid_raw = list_vertical_stems(outline, y=mid_y)
    single_stem = len(mid_capped) <= 1 and len(mid_raw) <= 1
    # Descenders (``y``/``g``/…): lower-band probes hit the tail hairline.
    # Sample the upper body (x-height band) instead of the ascender-safe fracs.
    if ymin < -40.0:
        fracs: tuple[float, ...] = (0.52, 0.58, 0.64, 0.72)
    elif h > 600.0 and single_stem:
        fracs = (0.16, 0.22, 0.28, 0.34, 0.40)
    else:
        fracs = (0.35, 0.42, 0.50, 0.58)
    widths: list[float] = []
    for f in fracs:
        y = ymin + f * h
        for span in list_vertical_stems(outline, y=y, max_width=frac_cap):
            widths.append(float(span.width))
    if not widths:
        raw: list[float] = []
        for f in fracs:
            y = ymin + f * h
            for span in list_vertical_stems(outline, y=y):
                raw.append(float(span.width))
        if not raw:
            raw = [float(s.width) for s in list_vertical_stems(outline)]
        if not raw:
            return None
        lo = min(raw)
        # Keep upright stems near the narrowest sample; drop bar/counter spans.
        cap = max(1.55 * lo, frac_cap)
        widths = [w for w in raw if w <= cap]
        if wmax > 2.2 * lo:
            widths = [w for w in widths if w < 0.55 * wmax]
        if not widths:
            widths = [lo]
    med = float(statistics.median(widths))
    core = [w for w in widths if 0.55 * med <= w <= 1.40 * med]
    return float(statistics.median(core)) if core else med



def _body_contrast_ratio(outline: Outline, stem_median: float | None) -> float | None:
    """Horizontal/vertical thickness ratio sampled in the body (not mid-ray noise).

    Rejects hairline crotch / join spans and **crown / baseline arches** so
    ``u`` / ``n`` / ``e`` are not falsely marked high-contrast when an H-probe
    clips the thin top arch instead of a designed horizontal bar.
    """
    if stem_median is None or stem_median <= 0.0:
        return None
    try:
        xmin, ymin, xmax, ymax = bounds(outline)
    except ValueError:
        return None
    w = max(xmax - xmin, 1.0)
    h = max(ymax - ymin, 1.0)
    y_lo = ymin + 0.18 * h
    y_hi = ymin + 0.72 * h
    hs: list[float] = []
    for f in (0.30, 0.40, 0.50, 0.60, 0.70):
        x = xmin + f * w
        for span in list_horizontal_stems(
            outline, x=x, max_width=1.8 * stem_median
        ):
            cy = float(span.center_y)
            if cy < y_lo or cy > y_hi:
                continue
            if 0.35 * stem_median <= span.width <= 1.8 * stem_median:
                hs.append(float(span.width))
    if not hs:
        return None
    return float(statistics.median(hs) / stem_median)



def _lower_stroke_cluster(widths: list[float]) -> float | None:
    """Median of the thin stroke cluster, splitting off join / crotch outliers.

    Sorted samples often show a gap between true diagonal stroke thickness and
    crotch / bar chords. Prefer the lower cluster when that gap is clear;
    otherwise the lower 40% (joins sit high).
    """
    if len(widths) < 2:
        return float(widths[0]) if widths else None
    ordered = sorted(widths)
    lim = max(2, int(0.75 * len(ordered)))
    region = ordered[:lim]
    gaps = [(region[i + 1] - region[i], i) for i in range(len(region) - 1)]
    gap, idx = max(gaps)
    med_all = float(statistics.median(ordered))
    if gap > 0.20 * med_all and idx + 1 >= 2:
        cluster = region[: idx + 1]
        return float(statistics.median(cluster))
    return float(statistics.median(ordered[: max(2, int(0.4 * len(ordered)))]))


def _oriented_stem_median(
    outline: Outline,
    *,
    stem_hint: float | None = None,
) -> float | None:
    """Median perpendicular stem via :func:`~typekernel.optics.stem.measure_oriented_stem`.

    Samples Latin diagonal bearings at body and **corner** origins so crossing
    letters (``x``) avoid the crotch join. A lower-stroke cluster drops join
    outliers. Returns ``None`` when no stable diagonal band is found.
    ``stem_hint`` (when set) only rejects extreme hairline / full-ink hits —
    it must not be an already-inflated upright or the thin cluster is lost.
    """
    from typekernel.optics.stem import measure_oriented_stem

    try:
        xmin, ymin, xmax, ymax = bounds(outline)
    except ValueError:
        return None
    w = max(xmax - xmin, 1.0)
    h = max(ymax - ymin, 1.0)
    ink = math.hypot(w, h)
    widths: list[float] = []
    bearings = (
        35.0,
        40.0,
        45.0,
        50.0,
        130.0,
        135.0,
        140.0,
        -35.0,
        -40.0,
        -45.0,
        -50.0,
    )
    origins = (
        (0.50, 0.50),
        (0.40, 0.45),
        (0.60, 0.55),
        (0.28, 0.28),
        (0.72, 0.72),
        (0.28, 0.72),
        (0.72, 0.28),
        (0.35, 0.65),
        (0.65, 0.35),
        (0.50, 0.40),
        (0.50, 0.60),
    )
    for deg in bearings:
        for fx, fy in origins:
            ox = xmin + fx * w
            oy = ymin + fy * h
            measured = measure_oriented_stem(outline, (ox, oy), deg)
            if measured is None:
                continue
            if measured >= 0.45 * ink:
                continue
            if (
                stem_hint is not None
                and stem_hint > 0.0
                and measured < 0.18 * stem_hint
            ):
                continue
            widths.append(float(measured))
    return _lower_stroke_cluster(widths)


def extract_glyph_style_metrics(glyph: ComposedGlyph) -> GlyphStyleMetrics:
    """Derive style proxies from a composed glyph's solid ink."""
    outline = _ink_outline(glyph)
    xmin, ymin, xmax, ymax = bounds(outline)
    pts = _sample_oncurve_points(outline)
    stem_median = _body_stem_median(outline)
    # Do not pass an upright hint into oriented sampling: inflated verticals
    # (heavy ``x``/``z``) would widen the accept band and hide the thin stroke
    # cluster. Hairline rejection uses ink-diagonal cap inside the sampler.
    oriented = _oriented_stem_median(outline, stem_hint=None)
    # Fall back only when vertical body probes miss. Inflation on ``x``/``z`` is
    # handled at compare time (needs a reference stem) via vertical_equiv.
    if stem_median is None and oriented is not None:
        from typekernel.optics.stem import vertical_equiv_from_diagonal

        stem_median = vertical_equiv_from_diagonal(oriented)
    # Prefer body-band contrast. No mid-ray fallback: single-stem letters
    # (l/i/v) yield bogus horizontal spans and must skip via missing.
    contrast = _body_contrast_ratio(outline, stem_median)
    w = max(xmax - xmin, 1.0)
    mid_y = 0.5 * (ymin + ymax)
    entry = _band_rail_y(pts, x0=xmin, x1=xmin + 0.20 * w)
    exit_y = _band_rail_y(pts, x0=xmax - 0.20 * w, x1=xmax)
    slant = _exit_slant_deg(pts, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)
    return GlyphStyleMetrics(
        stem_median=stem_median,
        contrast_ratio=contrast,
        ink_ymin=float(ymin),
        ink_ymax=float(ymax),
        ink_xmin=float(xmin),
        ink_xmax=float(xmax),
        entry_rail_y=entry,
        exit_rail_y=exit_y,
        exit_slant_deg=slant,
        bowl_center_y=float(mid_y),
        oriented_stem=oriented,
    )


def _check(
    name: str,
    ref: float | None,
    cand: float | None,
    limit: float,
    *,
    skip_if_missing: bool = True,
) -> StyleCheck:
    if ref is None or cand is None:
        ok = bool(skip_if_missing)
        return StyleCheck(
            name=name,
            reference=ref,
            candidate=cand,
            delta=None,
            limit=limit,
            ok=ok,
            note="skipped (missing measurement)" if skip_if_missing else "missing",
            hint="" if ok else fix_hint_for_check(name, ref, cand, ok=False),
        )
    delta = abs(cand - ref)
    ok = delta <= limit
    return StyleCheck(
        name=name,
        reference=ref,
        candidate=cand,
        delta=delta,
        limit=limit,
        ok=ok,
        hint=fix_hint_for_check(name, ref, cand, ok=ok),
    )


def compare_glyph_styles(
    reference: ComposedGlyph,
    candidate: ComposedGlyph,
    *,
    reference_name: str = "ref",
    candidate_name: str = "cand",
    tolerances: StyleConsistencyTolerances | None = None,
    skip_checks: Sequence[str] = (),
) -> StyleConsistencyReport:
    """Compare style proxies of ``candidate`` against ``reference``.

    Returns a structured report an agent can act on (which metric drifted).
    ``skip_checks`` names metrics to omit (e.g. rail Y when comparing a closed
    bowl ``o`` to an open script ``a``).
    """
    tol = tolerances or StyleConsistencyTolerances()
    ref_m = extract_glyph_style_metrics(reference)
    cand_m = extract_glyph_style_metrics(candidate)
    skip = frozenset(skip_checks)
    stem_limit = float(tol.stem_median)
    if (
        tol.stem_median_rel > 0.0
        and ref_m.stem_median is not None
        and abs(ref_m.stem_median) > 1e-9
    ):
        stem_limit = max(stem_limit, float(tol.stem_median_rel) * abs(ref_m.stem_median))
    # Crossing / flat-diagonal letters: mid-body vertical probes inflate at
    # heavy stems (crotch / diagonal-as-vertical). When the upright drifts past
    # the reference, gate via oriented thickness mapped back to vertical
    # equivalent with :func:`~typekernel.optics.stem.vertical_equiv_from_diagonal`
    # (same transform as construction compensation).
    _crossing = frozenset({"x", "X", "z", "Z"})
    cand_stem = cand_m.stem_median
    if (
        candidate_name in _crossing
        and ref_m.stem_median is not None
        and cand_m.oriented_stem is not None
        and (
            cand_m.stem_median is None
            or cand_m.stem_median > 1.18 * abs(ref_m.stem_median)
        )
    ):
        from typekernel.optics.stem import vertical_equiv_from_diagonal

        cand_stem = vertical_equiv_from_diagonal(cand_m.oriented_stem)

    checks_list: list[StyleCheck] = [
        _check("stem_median", ref_m.stem_median, cand_stem, stem_limit),
        _check(
            "contrast_ratio",
            ref_m.contrast_ratio,
            cand_m.contrast_ratio,
            tol.contrast_ratio,
        ),
        _check("entry_rail_y", ref_m.entry_rail_y, cand_m.entry_rail_y, tol.entry_rail_y),
        _check("exit_rail_y", ref_m.exit_rail_y, cand_m.exit_rail_y, tol.exit_rail_y),
        _check(
            "exit_slant_deg",
            ref_m.exit_slant_deg,
            cand_m.exit_slant_deg,
            tol.exit_slant_deg,
        ),
        _check(
            "bowl_center_y",
            ref_m.bowl_center_y,
            cand_m.bowl_center_y,
            tol.bowl_center_y,
        ),
        _check("ink_ymin", ref_m.ink_ymin, cand_m.ink_ymin, tol.ink_ymin),
        # Caps / ascenders may exceed control x-height — wider budget.
        _check("ink_ymax", ref_m.ink_ymax, cand_m.ink_ymax, tol.ink_ymax),
    ]
    # Oriented stem: only for stable diagonal letter pairs (``v``/``w``). Script
    # bowls can spuriously measure an oriented band; do not gate those.
    _oriented_letters = frozenset({"v", "w", "V", "W"})
    if (
        ref_m.oriented_stem is not None
        and cand_m.oriented_stem is not None
        and reference_name in _oriented_letters
        and candidate_name in _oriented_letters
    ):
        checks_list.append(
            _check(
                "oriented_stem",
                ref_m.oriented_stem,
                cand_m.oriented_stem,
                stem_limit,
                skip_if_missing=False,
            )
        )
    if skip:
        checks_list = [c for c in checks_list if c.name not in skip]
    checks = tuple(checks_list)
    return StyleConsistencyReport(
        reference_name=reference_name,
        candidate_name=candidate_name,
        checks=checks,
        passed=all(c.ok for c in checks),
        reference=ref_m,
        candidate=cand_m,
    )


@dataclass(frozen=True, slots=True)
class SequenceStyleReport:
    """Results of walking a designer-order glyph sequence."""

    order: tuple[str, ...]
    control: str
    reports: tuple[StyleConsistencyReport, ...]
    passed: bool
    unlocked: tuple[str, ...]

    @property
    def failures(self) -> tuple[StyleConsistencyReport, ...]:
        return tuple(r for r in self.reports if not r.passed)


def check_design_sequence(
    glyphs: Mapping[str, ComposedGlyph],
    order: Sequence[str],
    *,
    control: str | None = None,
    tolerances: StyleConsistencyTolerances | None = None,
    compare_to_previous: bool = True,
    skip_checks_for_pair: Callable[[str, str], Sequence[str]] | None = None,
) -> SequenceStyleReport:
    """Gate a charset built in designer order.

    For each glyph after the control, compare against the **control** and
    (when ``compare_to_previous``) the immediately previous unlocked glyph.
    Both comparisons must pass to unlock the letter.

    ``skip_checks_for_pair`` if set is ``(ref_name, cand_name) -> skip names``.
    """
    if not order:
        raise ValueError("design order is empty")
    missing = [ch for ch in order if ch not in glyphs]
    if missing:
        raise KeyError(f"glyphs missing from map: {missing!r}")
    control_ch = control if control is not None else order[0]
    if control_ch not in glyphs:
        raise KeyError(f"control glyph {control_ch!r} not in map")
    tol = tolerances or StyleConsistencyTolerances()
    reports: list[StyleConsistencyReport] = []
    unlocked: list[str] = [control_ch]
    for ch in order:
        if ch == control_ch:
            continue
        skip_c: Sequence[str] = ()
        if skip_checks_for_pair is not None:
            skip_c = tuple(skip_checks_for_pair(control_ch, ch) or ())
        ref_control = compare_glyph_styles(
            glyphs[control_ch],
            glyphs[ch],
            reference_name=control_ch,
            candidate_name=ch,
            tolerances=tol,
            skip_checks=skip_c,
        )
        reports.append(ref_control)
        ok = ref_control.passed
        if compare_to_previous and unlocked:
            prev = unlocked[-1]
            if prev != control_ch:
                skip_p: Sequence[str] = ()
                if skip_checks_for_pair is not None:
                    skip_p = tuple(skip_checks_for_pair(prev, ch) or ())
                ref_prev = compare_glyph_styles(
                    glyphs[prev],
                    glyphs[ch],
                    reference_name=prev,
                    candidate_name=ch,
                    tolerances=tol,
                    skip_checks=skip_p,
                )
                reports.append(ref_prev)
                ok = ok and ref_prev.passed
        if ok:
            unlocked.append(ch)
    return SequenceStyleReport(
        order=tuple(order),
        control=control_ch,
        reports=tuple(reports),
        passed=all(r.passed for r in reports),
        unlocked=tuple(unlocked),
    )

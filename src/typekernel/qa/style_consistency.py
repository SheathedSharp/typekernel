"""Adjacent / sequential glyph style consistency (designer-order gate).

Human type design proceeds **one glyph at a time**, checking the new letter
against control and previously unlocked letters. A brief phrase is a late
specimen — not the design method.

This module works on abstract :class:`~typekernel.parts.compose.ComposedGlyph`
outlines (FormSources-derived **or** skeleton / ``trace_letter`` faces).
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
    "script_sequence_tolerances",
    "script_topology_skip_checks",
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
    # True descenders (``y``/``g``/…, ymin ≲ −100): lower-band probes hit the
    # tail hairline — sample the x-height band instead. Tall single stems
    # (caps / ascenders, ``ymax`` above x-height) use the lower body so
    # ``E``/``Y`` bars and crotches are not mistaken for stems. Body rounds
    # with overshoot can have ``h>600`` while ``ymax`` stays near x-height —
    # keep them on the mid band (open ``c``/``e`` shoulders).
    if ymin < -100.0:
        fracs: tuple[float, ...] = (0.52, 0.58, 0.64, 0.72)
    elif ymax > 650.0 and single_stem:
        lower = (0.16, 0.22, 0.28, 0.34, 0.40)
        # Diagonals (``V``/``A``): a *single* span that widens upward toward
        # the crotch. Multi-span rows (``M``/``B``) and bottom-heavy hooks
        # (``J``) stay on the lower band.
        lower_hi: list[float] = []
        lower_all_single = True
        for lf in lower:
            spans = list_vertical_stems(outline, y=ymin + lf * h)
            if not spans:
                continue
            if len(spans) > 1:
                lower_all_single = False
            lower_hi.append(max(float(s.width) for s in spans))
        if (
            lower_all_single
            and len(lower_hi) >= 2
            and max(lower_hi) > 1.35 * min(lower_hi)
            and lower_hi[-1] >= 1.2 * lower_hi[0]
        ):
            fracs = (0.62, 0.68, 0.74, 0.80)
        else:
            fracs = lower
    else:
        fracs = (0.35, 0.42, 0.50, 0.58)
    widths: list[float] = []
    chord_cap = 0.72 * wmax
    speck = 0.06 * wmax
    for f in fracs:
        y = ymin + f * h
        capped = list_vertical_stems(outline, y=y, max_width=frac_cap)
        raw = [
            s
            for s in list_vertical_stems(outline, y=y)
            if speck <= float(s.width) < chord_cap
        ]
        if capped and raw:
            cap_hi = max(float(s.width) for s in capped)
            raw_hi = max(float(s.width) for s in raw)
            # Cap kept only aperture hairline while upright exceeds 0.42×ink.
            # Require a true hairline (≤0.15×ink) so bowl chords (``G``) do not
            # trigger a back-stem rescue over a real upright.
            if cap_hi < 0.40 * raw_hi and cap_hi <= 0.12 * wmax:
                widths.append(raw_hi)
            elif len(capped) >= 2:
                lo = min(float(s.width) for s in capped)
                hi = cap_hi
                # Only the two-span hairline+upright case prefers ``hi``.
                # Crowded script scans (many stems) must keep the cluster.
                if (
                    len(capped) == 2
                    and hi >= 2.2 * lo
                    and lo <= 0.12 * wmax
                ):
                    widths.append(hi)
                else:
                    caps_w = [float(s.width) for s in capped]
                    if len(caps_w) >= 3:
                        med_c = float(statistics.median(caps_w))
                        caps_w = [cw for cw in caps_w if cw >= 0.70 * med_c]
                    widths.extend(caps_w)
            else:
                widths.append(cap_hi)
        elif raw:
            # Uncapped-only path: allow back stems up to half the ink width
            # (black open rounds). Reject wider diagonal crotches (``A``/``V``).
            raw_hi = max(float(s.width) for s in raw)
            if raw_hi <= 0.55 * wmax:
                widths.append(raw_hi)
        elif capped:
            widths.extend(float(s.width) for s in capped)
    if not widths:
        fallback: list[float] = []
        for f in fracs:
            y = ymin + f * h
            for span in list_vertical_stems(outline, y=y):
                fallback.append(float(span.width))
        if not fallback:
            fallback = [float(s.width) for s in list_vertical_stems(outline)]
        if not fallback:
            return None
        lo = min(fallback)
        # Keep upright stems near the narrowest sample; drop bar/counter spans.
        cap = max(1.55 * lo, frac_cap)
        widths = [w for w in fallback if w <= cap]
        if wmax > 2.2 * lo:
            widths = [w for w in widths if w < 0.55 * wmax]
        if not widths:
            widths = [lo]
    # Prefer the narrow upright cluster when crotches/bars mix in (``V``/``M``).
    # Do not drop a real stem in favor of bowl hairlines (thin ``b``/``d``).
    if len(widths) >= 2 and max(widths) > 1.50 * min(widths):
        lo_w = min(widths)
        hi_w = max(widths)
        mid_w = float(statistics.median(widths))
        if hi_w >= 0.40 * wmax or hi_w >= 1.8 * mid_w:
            narrow = [w for w in widths if w <= 1.35 * lo_w]
            if narrow and float(statistics.median(narrow)) >= 0.75 * mid_w:
                widths = narrow
    med = float(statistics.median(widths))
    core = [w for w in widths if 0.55 * med <= w <= 1.40 * med]
    med = float(statistics.median(core)) if core else med

    # Back-stem / aperture rescue: at black weights the real upright is often
    # wider than ``0.42×ink`` (open ``c``/``e``), so the cap keeps only the
    # aperture hairline. Prefer the thickest non-chord span per scanline.
    chord_cap = 0.72 * wmax
    speck = 0.06 * wmax
    back_widths: list[float] = []
    for f in fracs:
        y = ymin + f * h
        spans = [
            s
            for s in list_vertical_stems(outline, y=y)
            if speck <= float(s.width) < chord_cap
        ]
        if not spans:
            continue
        back_widths.append(float(max(spans, key=lambda s: s.width).width))
    if len(back_widths) >= 2:
        back = float(statistics.median(back_widths))
        # Only rescue aperture-hairline pollution — never inflate diagonals
        # (``w``/``v``) or lone crotch chords (script ``y``). Require ≥2
        # agreeing scans so a single thick ray cannot override the cluster.
        if med < 0.40 * back and med <= 0.15 * wmax:
            bcore = [w for w in back_widths if 0.55 * back <= w <= 1.40 * back]
            return float(statistics.median(bcore)) if bcore else back
    return med



def _body_contrast_ratio(outline: Outline, stem_median: float | None) -> float | None:
    """Horizontal/vertical thickness ratio (crossbar or round-polar thins).

    Mid-band H probes catch designed bars (``H``/``e``) and reject crown /
    baseline arches on ``n``/``u``. Closed bowls (``O``/``o``/``0``) put their
    designed thins at the poles — when *both* crown and baseline yield spans,
    those polar thins over side uprights are the contrast ratio. A lone crown (shoulder arch) is ignored so ``n`` stays contrast-null;
    base-only with ≥2 mid uprights covers ``U``. ``R`` narrows bar-vs-join
    body samples when polar is unavailable. If the mid-band median is join-inflated vs polar (>1.15×), prefer polar.
    Open ``e`` midbars that collapse below 0.65×polar (black eye aperture)
    also fall back to polar.
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
    body: list[float] = []
    midbar: list[float] = []
    crown: list[float] = []
    base: list[float] = []
    for f in (0.30, 0.40, 0.50, 0.60, 0.70):
        x = xmin + f * w
        for hspan in list_horizontal_stems(
            outline, x=x, max_width=2.2 * stem_median
        ):
            cy = float(hspan.center_y)
            ww = float(hspan.width)
            if ww < 0.25 * stem_median:
                continue
            if y_lo <= cy <= y_hi and ww <= 1.8 * stem_median:
                body.append(ww)
                # Open ``e`` eye bar sits near mid body.
                if ymin + 0.40 * h <= cy <= ymin + 0.60 * h:
                    midbar.append(ww)
            if cy <= ymin + 0.28 * h and ww <= 2.0 * stem_median:
                base.append(ww)
            if cy >= ymax - 0.28 * h and ww <= 2.0 * stem_median:
                crown.append(ww)
    # Side uprights as denominator for polar thins (open ``C`` stem_median can
    # under-read; mid V spans stay near the designed thick).
    v_spans: list[float] = []
    for f in (0.42, 0.50, 0.58):
        for vspan in list_vertical_stems(outline, y=ymin + f * h):
            ww = float(vspan.width)
            if 0.35 * stem_median <= ww <= 1.8 * stem_median:
                v_spans.append(ww)
    mid_stemlike = [
        s
        for s in list_vertical_stems(outline, y=ymin + 0.50 * h)
        if 0.35 * stem_median <= float(s.width) <= 1.8 * stem_median
    ]
    multi_v = len(mid_stemlike) >= 2
    v_den = float(statistics.median(v_spans)) if v_spans else float(stem_median)

    def _ratio(xs: list[float], den: float) -> float | None:
        return float(statistics.median(xs) / den) if xs else None

    # Polar: both poles (``O``) or base-only with ≥2 mid uprights (``U``).
    if crown and base:
        polar_r = _ratio(crown + base, v_den)
    elif base and multi_v and not crown:
        polar_r = _ratio(base, v_den)
    else:
        polar_r = None
    # ``R`` bar vs leg-join: narrow body only when polar is unavailable.
    if polar_r is None and len(body) >= 2 and max(body) > 1.25 * min(body):
        lo = min(body)
        narrow = [bw for bw in body if bw <= 1.35 * lo]
        if narrow:
            body = narrow
    body_r = _ratio(body, float(stem_median))
    mid_r = _ratio(midbar, float(stem_median))
    # Black ``e``: midbar can read aperture hairline while poles still track the
    # designed thick — prefer polar when midbar collapses below 0.65×polar.
    if mid_r is not None and polar_r is not None and mid_r < 0.65 * polar_r:
        return polar_r
    if body_r is not None and polar_r is not None:
        # Join-inflated body OR over-narrow spur vs polar → trust poles.
        if body_r > 1.15 * polar_r or body_r < 0.70 * polar_r:
            return polar_r
        return body_r
    if body_r is not None:
        return body_r
    return polar_r



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


def _estimate_diagonal_angle_from_vertical(outline: Outline) -> float | None:
    """Angle-from-vertical of a single drifting diagonal (``z``) via span centres.

    Mid-body vertical spans on a ``z`` diagonal migrate horizontally with Y.
    Fitting that drift recovers the construction angle so
    :func:`~typekernel.optics.stem.vertical_equiv_from_diagonal` inverts the
    same compensation the glyph was built with. Crossed diagonals (``x``)
    cancel and return near 0 — callers should fall back to 45°.
    """
    try:
        xmin, ymin, xmax, ymax = bounds(outline)
    except ValueError:
        return None
    h = max(ymax - ymin, 1.0)
    wmax = max(xmax - xmin, 1.0)
    chord_cap = 0.72 * wmax
    pts: list[tuple[float, float]] = []
    for f in (0.35, 0.42, 0.50, 0.58, 0.65):
        spans = [
            s
            for s in list_vertical_stems(outline, y=ymin + f * h)
            if float(s.width) < chord_cap
        ]
        if not spans:
            continue
        s = max(spans, key=lambda sp: float(sp.width))
        pts.append((f, 0.5 * (float(s.left) + float(s.right))))
    if len(pts) < 3:
        return None
    fs = [p[0] for p in pts]
    xs = [p[1] for p in pts]
    fmean = statistics.mean(fs)
    xmean = statistics.mean(xs)
    den = sum((f - fmean) ** 2 for f in fs)
    if den < 1e-12:
        return None
    dx_df = sum((f - fmean) * (x - xmean) for f, x in zip(fs, xs)) / den
    # dy = df * h  →  dx/dy = (dx_df * df) / (df * h) = dx_df / h
    return float(math.degrees(math.atan(abs(dx_df) / h)))


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

        phi = _estimate_diagonal_angle_from_vertical(outline)
        if phi is None or phi < 25.0 or phi > 80.0:
            phi = 45.0
        ctx_contrast = float(getattr(glyph.context, "contrast", 1.0) or 1.0)
        stem_median = vertical_equiv_from_diagonal(
            oriented, phi, contrast=ctx_contrast
        )
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
    # Diagonals whose mid-band vertical probes inflate at heavy stems / slab
    # feet. Remap via oriented → vertical_equiv (same as construction).
    _crossing = frozenset({"x", "X", "z", "Z", "v", "w", "y", "k", "V", "W", "Y", "K", "A", "M", "N"})
    cand_stem = cand_m.stem_median
    if (
        candidate_name in _crossing
        and ref_m.stem_median is not None
        and cand_m.oriented_stem is not None
        and (
            cand_m.stem_median is None
            or cand_m.stem_median > 1.18 * abs(ref_m.stem_median)
            or cand_m.stem_median < abs(ref_m.stem_median) / 1.18
        )
    ):
        from typekernel.optics.stem import vertical_equiv_from_diagonal

        # Invert compensation at the glyph's diagonal angle (default 45° is
        # wrong for black ``z``, whose bars flatten the stroke toward ~65–70°).
        cand_outline = _ink_outline(candidate)
        phi = _estimate_diagonal_angle_from_vertical(cand_outline)
        if phi is None or phi < 25.0 or phi > 80.0:
            phi = 45.0
        contrast = float(getattr(candidate.context, "contrast", 1.0) or 1.0)
        ve = vertical_equiv_from_diagonal(
            cand_m.oriented_stem, phi, contrast=contrast
        )
        # Prefer the probe closer to the reference stem. Include raw oriented
        # thickness: crossed ``X``/``M`` often have φ≈0 so VE-at-45° overshoots,
        # while oriented itself tracks the diagonal stroke near ``H``.
        raw = cand_m.stem_median
        ref_abs = abs(ref_m.stem_median)
        opts: list[float] = [ve]
        if raw is not None:
            opts.append(float(raw))
        opts.append(float(cand_m.oriented_stem))
        cand_stem = min(opts, key=lambda v: abs(v - ref_abs))

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


# --- Script face topology skips / tolerances (no DesignSequence gate) ---

_SCRIPT_CLOSED_BOWLS: frozenset[str] = frozenset({"o", "O"})
_SCRIPT_ASCENDERS: frozenset[str] = frozenset(
    {"d", "h", "D", "l", "b", "k", "f", "t"}
)
_SCRIPT_DESCENDERS: frozenset[str] = frozenset({"j", "y", "g", "p", "q"})
_SCRIPT_DOTTED: frozenset[str] = frozenset({"i", "j"})


def script_topology_skip_checks(ref: str, cand: str) -> tuple[str, ...]:
    """Metric skips across script topology roles (rails stay meaningful).

    Unlike :func:`latin_topology_skip_checks`, entry/exit rails and exit slant
    are **gated** for same-role body letters — they are the writing-connection
    language. Closed bowls omit rails; ascenders/descenders/dotted letters omit
    extents and rail metrics that topology makes meaningless.
    """
    skip: list[str] = []
    if ref in _SCRIPT_CLOSED_BOWLS or cand in _SCRIPT_CLOSED_BOWLS:
        skip.extend(["entry_rail_y", "exit_rail_y", "exit_slant_deg"])
    if cand in _SCRIPT_ASCENDERS or ref in _SCRIPT_ASCENDERS:
        skip.extend(["ink_ymax", "bowl_center_y", "exit_rail_y", "exit_slant_deg"])
    if cand in _SCRIPT_DESCENDERS or ref in _SCRIPT_DESCENDERS:
        # Descender loops poison lower-band exit-angle samples.
        skip.extend(["ink_ymin", "bowl_center_y", "entry_rail_y", "exit_slant_deg"])
    if cand in _SCRIPT_DOTTED or ref in _SCRIPT_DOTTED:
        # Single stem + tittle: vertical-stem probes are not comparable to
        # dual-stem body letters.
        skip.extend(
            [
                "exit_rail_y",
                "exit_slant_deg",
                "ink_ymax",
                "bowl_center_y",
                "stem_median",
            ]
        )
    return tuple(dict.fromkeys(skip))


def script_sequence_tolerances() -> StyleConsistencyTolerances:
    """Budgets for full script style-check walk (control → charset).

    Rails/slant/stem stay near body defaults. Contrast is wider than
    :func:`~typekernel.qa.style_consistency.script_body_tolerances` to allow
    multi-vertical pen stress (``u``/``h``) without phrase-batch fudge — still
    paired with :func:`script_topology_skip_checks`, not a blank cheque.
    Same-role pairs (``a`` vs ``e``) should prefer ``script_body_tolerances``.
    """
    return StyleConsistencyTolerances(
        stem_median=14.0,
        contrast_ratio=0.95,
        entry_rail_y=40.0,
        exit_rail_y=42.0,
        exit_slant_deg=40.0,
        bowl_center_y=55.0,
        ink_ymin=55.0,
        ink_ymax=120.0,
    )


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

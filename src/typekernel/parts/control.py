"""Control glyphs and related forms — type-designer workflow.

Order: proportions (:class:`~typekernel.parts.context.DesignContext`) →
control letters as **continuous cubic outlines** → derive related forms →
optical / class spacing (elsewhere).

Each control glyph is drawn from a design record (:class:`NMetrics` for the
``n`` family, :class:`OMetrics` for the ``o`` family) and carries it as
``ComposedGlyph.design``. Related forms read that record from the control
glyph, so tuning the control (``n_metrics(ctx).tuned(counter=...)``) carries
through to ``h``, ``u``, ``i``, ``l`` without touching the context.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

from fontTools.misc.bezierTools import splitCubic

from typekernel.geo.contour import reverse_contour, signed_area
from typekernel.geo.curves import superellipse_cubics
from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.path_helpers import KAPPA
from typekernel.geo.point import Point
from typekernel.parts.compose import ComposedGlyph, GlyphAssembler
from typekernel.parts.context import DesignContext
from typekernel.parts.primitives import bowl, tittle, vertical_stem
from typekernel.parts.transforms import mirror_x, mirror_y

__all__ = [
    "NMetrics",
    "OMetrics",
    "a_from_o",
    "b_from_o",
    "build_control_letter",
    "build_control_word",
    "build_h",
    "build_i",
    "build_m",
    "build_n",
    "build_o",
    "build_r",
    "build_u",
    "c_from_o",
    "d_from_o",
    "e_from_o",
    "h_from_n",
    "i_from_n",
    "l_from_n",
    "m_from_n",
    "n_metrics",
    "o_metrics",
    "p_from_o",
    "q_from_o",
    "r_from_n",
    "u_from_n",
]

Pt = tuple[float, float]
Cubic = tuple[Pt, Pt, Pt, Pt]


@dataclass(frozen=True, slots=True)
class NMetrics:
    """Design record for the ``n`` family (``n h m r u i l``).

    Attributes:
        stem: Vertical stem thickness.
        counter: Inner face to inner face of the ``n`` counter.
        x_height: Flat top of the left stem.
        ascender: Top of ascending stems (``h``, ``l``).
        overshoot: How far round extrema pass the zones.
        crown_y: Outer shoulder peak.
        leg_top: Where the outer shoulder lands on the right leg.
        join_y: Inner crotch height where the counter springs from the stems.
        inner_crown: Counter peak under the shoulder (``crown_y - inner_crown``
            is the shoulder thickness).
        kappa: Shoulder handle ratio (tension).
    """

    stem: float
    counter: float
    x_height: float
    ascender: float
    overshoot: float
    crown_y: float
    leg_top: float
    join_y: float
    kappa: float
    inner_crown: float

    @property
    def shoulder_thickness(self) -> float:
        return self.crown_y - self.inner_crown

    @property
    def width(self) -> float:
        """Ink width of ``n``: two stems around one counter."""
        return 2.0 * self.stem + self.counter

    def tuned(self, **kwargs: float) -> NMetrics:
        """Copy with selected fields overridden (designer adjustment)."""
        return replace(self, **kwargs)


def n_metrics(ctx: DesignContext) -> NMetrics:
    """Derive the ``n`` design record from family proportions."""
    stem = ctx.stem
    counter = ctx.x_height * (0.46 + 0.12 * ctx.aperture)
    # Slightly flatter shoulder when roundness is low (coding); rounder when soft.
    kappa = KAPPA * (0.92 + 0.28 * ctx.roundness)
    crown_y = ctx.x_height + ctx.overshoot
    # Outer meet: just under x-height so crown overshoots; inner join lower.
    leg_top = ctx.x_height - stem * 0.02
    join_y = ctx.x_height * (0.50 + 0.04 * ctx.roundness)
    inner_crown = crown_y - stem * (0.92 + 0.08 * ctx.contrast)
    inner_crown = min(inner_crown, crown_y - stem * 0.75)
    inner_crown = max(inner_crown, join_y + stem * 0.35)
    return NMetrics(
        stem=stem,
        counter=counter,
        x_height=ctx.x_height,
        ascender=ctx.ascender,
        overshoot=ctx.overshoot,
        crown_y=crown_y,
        leg_top=leg_top,
        join_y=join_y,
        kappa=kappa,
        inner_crown=inner_crown,
    )


@dataclass(frozen=True, slots=True)
class OMetrics:
    """Design record for the ``o`` family (``o b d p q``).

    The bowl is a superellipse ring centred at ``(rx, x_height / 2)``.
    """

    rx: float
    ry: float
    thickness: float
    exponent: float
    x_height: float
    overshoot: float

    @property
    def width(self) -> float:
        return 2.0 * self.rx

    def tuned(self, **kwargs: float) -> OMetrics:
        return replace(self, **kwargs)


def o_metrics(ctx: DesignContext) -> OMetrics:
    """Derive the ``o`` design record from family proportions."""
    ry = ctx.x_height / 2.0 + ctx.overshoot
    rx = ry * (0.88 + 0.10 * ctx.aperture)
    # Squircle when roundness low (coding); ellipse when soft.
    exponent = 2.0 + 0.7 * (1.0 - max(0.0, min(1.0, ctx.roundness)))
    return OMetrics(
        rx=rx,
        ry=ry,
        thickness=ctx.stem,
        exponent=exponent,
        x_height=ctx.x_height,
        overshoot=ctx.overshoot,
    )


def _n_record(glyph: ComposedGlyph) -> NMetrics:
    return glyph.design if isinstance(glyph.design, NMetrics) else n_metrics(glyph.context)


def _o_record(glyph: ComposedGlyph) -> OMetrics:
    return glyph.design if isinstance(glyph.design, OMetrics) else o_metrics(glyph.context)


# --- shoulder geometry ------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _Shoulder:
    """Named cubics of an ``n`` shoulder in ``n`` coordinates (left stem at x=0).

    ``outer`` runs left spring → crown → right leg top; ``inner`` runs right
    join → inner crown → left join. ``r`` and ``m`` reuse these curves.
    """

    outer: tuple[Cubic, Cubic]
    inner: tuple[Cubic, Cubic]
    l0: float
    l1: float
    r0: float
    r1: float


def _shoulder(m: NMetrics, x0: float = 0.0) -> _Shoulder:
    t, w, k = m.stem, m.counter, m.kappa
    l0, l1 = x0, x0 + t
    r0, r1 = x0 + t + w, x0 + t + w + t
    mid = (l1 + r0) / 2.0
    crown, leg_top, join, ic = m.crown_y, m.leg_top, m.join_y, m.inner_crown
    spring = m.x_height
    outer = (
        ((l1, spring), (l1, spring + k * (crown - spring)), (mid - k * (mid - l1), crown), (mid, crown)),
        ((mid, crown), (mid + k * (r1 - mid), crown), (r1, leg_top + k * (crown - leg_top)), (r1, leg_top)),
    )
    inner = (
        ((r0, join), (r0, join + k * (ic - join)), (mid + k * (r0 - mid), ic), (mid, ic)),
        ((mid, ic), (mid - k * (mid - l1), ic), (l1, join + k * (ic - join)), (l1, join)),
    )
    return _Shoulder(outer, inner, l0, l1, r0, r1)


def _curve(b: PathBuilder, c: Cubic) -> None:
    b.curveTo(c[1][0], c[1][1], c[2][0], c[2][1], c[3][0], c[3][1])


def _split(c: Cubic, where: float, *, horizontal: bool) -> tuple[Cubic, Cubic] | None:
    """Split ``c`` where it crosses ``x = where`` (or ``y`` if ``horizontal``)."""
    pieces = splitCubic(*c, where, horizontal)
    if len(pieces) != 2:
        return None
    a, b = pieces
    return (tuple(a), tuple(b))


def _ccw(outline: Outline) -> Outline:
    """Font convention: outer contour CCW (positive signed area)."""
    c0 = outline.contours[0]
    if signed_area(c0) < 0:
        return Outline((reverse_contour(c0),))
    return outline


def _n_family_outline(m: NMetrics, *, left_top: float) -> Outline:
    """One continuous outer contour: left stem + shoulder + right leg.

    No third ``arch`` mesh and no ``union``. The counter is the notch formed
    by the stem insides and the inner shoulder.
    """
    s = _shoulder(m)
    b = PathBuilder()
    b.moveTo(s.l0, 0.0)
    b.lineTo(s.l0, left_top)
    b.lineTo(s.l1, left_top)
    if left_top > m.x_height + 0.5:
        # h: down the right face of the ascender stem to the shoulder spring
        b.lineTo(s.l1, m.x_height)
    _curve(b, s.outer[0])
    _curve(b, s.outer[1])
    b.lineTo(s.r1, 0.0)
    b.lineTo(s.r0, 0.0)
    b.lineTo(s.r0, m.join_y)
    _curve(b, s.inner[0])
    _curve(b, s.inner[1])
    b.lineTo(s.l1, 0.0)
    b.closePath()
    return _ccw(b.build())


def _pack(
    ctx: DesignContext,
    record: object,
    anchors: dict[str, Pt],
    *outlines: Outline,
) -> ComposedGlyph:
    """Sidebearing pack; single outline — no boolean letter topology."""
    asm = GlyphAssembler(ctx).with_design(record)
    for o in outlines:
        asm.add(o)
    for name, (x, y) in anchors.items():
        asm.anchor(name, x, y)
    return asm.build()


# --- n family -----------------------------------------------------------------


def build_n(ctx: DesignContext, metrics: NMetrics | None = None) -> ComposedGlyph:
    """Control ``n``: continuous cubic outline from its design record."""
    m = metrics or n_metrics(ctx)
    cx = m.width / 2.0
    anchors = {"top": (cx, m.x_height), "bottom": (cx, 0.0)}
    return _pack(ctx, m, anchors, _n_family_outline(m, left_top=m.x_height))


def build_h(ctx: DesignContext, metrics: NMetrics | None = None) -> ComposedGlyph:
    """``h`` from the same shoulder/leg recipe as ``n`` (ascender left stem)."""
    m = metrics or n_metrics(ctx)
    anchors = {"top": (m.stem / 2.0, m.ascender), "bottom": (m.width / 2.0, 0.0)}
    return _pack(ctx, m, anchors, _n_family_outline(m, left_top=m.ascender))


def h_from_n(n_glyph: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    """Derive ``h`` from control ``n``: same shoulder and leg, ascending stem.

    Reads the ``n`` design record carried on ``n_glyph``, so a tuned ``n``
    yields a matching ``h``.
    """
    return build_h(ctx or n_glyph.context, _n_record(n_glyph))


def r_from_n(
    n_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    arm: float = 0.5,
) -> ComposedGlyph:
    """Derive ``r``: the ``n`` stem and shoulder, cut off at a vertical terminal.

    ``arm`` places the terminal between the counter's centre (``0``) and the
    right leg's inner face (``1``). Outer and inner shoulder curves are split
    at that x, so the arm is literally the ``n`` shoulder, truncated.
    """
    if not 0.0 < arm < 1.0:
        raise ValueError(f"arm must be in (0, 1), got {arm}")
    c = ctx or n_glyph.context
    m = _n_record(n_glyph)
    s = _shoulder(m)
    mid = s.outer[0][3][0]
    x_t = mid + arm * (s.r0 - mid)
    outer = _split(s.outer[1], x_t, horizontal=False)
    inner = _split(s.inner[0], x_t, horizontal=False)
    if outer is None or inner is None:  # pragma: no cover - monotonic by construction
        raise ValueError("shoulder does not cross the terminal position")

    b = PathBuilder()
    b.moveTo(s.l0, 0.0)
    b.lineTo(s.l0, m.x_height)
    b.lineTo(s.l1, m.x_height)
    _curve(b, s.outer[0])
    _curve(b, outer[0])
    b.lineTo(*inner[1][0])
    _curve(b, inner[1])
    _curve(b, s.inner[1])
    b.lineTo(s.l1, 0.0)
    b.closePath()
    anchors = {"top": (x_t / 2.0, m.x_height), "bottom": (m.stem / 2.0, 0.0)}
    return _pack(c, m, anchors, _ccw(b.build()))


def build_r(ctx: DesignContext, metrics: NMetrics | None = None) -> ComposedGlyph:
    return r_from_n(build_n(ctx, metrics), ctx)


def m_from_n(
    n_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    counter_scale: float = 0.92,
) -> ComposedGlyph:
    """Derive ``m``: two ``n`` shoulders sharing the middle stem.

    Each counter is ``counter_scale`` of the ``n`` counter (designers narrow
    ``m`` so its colour matches ``n``). The first arch is cut where it comes
    down to the middle stem's top, which forms the crotch; one continuous
    contour, no boolean union.
    """
    if counter_scale <= 0:
        raise ValueError(f"counter_scale must be positive, got {counter_scale}")
    c = ctx or n_glyph.context
    m = _n_record(n_glyph)
    mm = m.tuned(counter=m.counter * counter_scale)
    s1 = _shoulder(mm)
    s2 = _shoulder(mm, s1.r0)
    xh = mm.x_height

    b = PathBuilder()
    b.moveTo(s1.l0, 0.0)
    b.lineTo(s1.l0, xh)
    b.lineTo(s1.l1, xh)
    _curve(b, s1.outer[0])
    descent = _split(s1.outer[1], xh, horizontal=True)
    if descent is not None:
        a = descent[0]
        _curve(b, (a[0], a[1], a[2], (a[3][0], xh)))
    b.lineTo(s2.l1, xh)
    _curve(b, s2.outer[0])
    _curve(b, s2.outer[1])
    b.lineTo(s2.r1, 0.0)
    b.lineTo(s2.r0, 0.0)
    b.lineTo(s2.r0, mm.join_y)
    _curve(b, s2.inner[0])
    _curve(b, s2.inner[1])
    b.lineTo(s2.l1, 0.0)
    b.lineTo(s1.r0, 0.0)
    b.lineTo(s1.r0, mm.join_y)
    _curve(b, s1.inner[0])
    _curve(b, s1.inner[1])
    b.lineTo(s1.l1, 0.0)
    b.closePath()
    cx = s2.r1 / 2.0
    anchors = {"top": (cx, xh), "bottom": (cx, 0.0)}
    return _pack(c, m, anchors, _ccw(b.build()))


def build_m(ctx: DesignContext, metrics: NMetrics | None = None) -> ComposedGlyph:
    return m_from_n(build_n(ctx, metrics), ctx)


def build_u(ctx: DesignContext, metrics: NMetrics | None = None) -> ComposedGlyph:
    """``u`` related to ``n``: the ``n`` turned through 180°."""
    return u_from_n(build_n(ctx, metrics), ctx)


def u_from_n(n_glyph: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    """Derive ``u``: the ``n`` outline turned through 180°.

    The shoulder becomes the bowl (its crown overshoot now dips below the
    baseline) and the ``n``'s full left stem becomes the right stem that
    runs down to the baseline.
    """
    c = ctx or n_glyph.context
    m = _n_record(n_glyph)
    cx, cy = m.width / 2.0, m.x_height / 2.0
    turned = mirror_y(mirror_x(_n_family_outline(m, left_top=m.x_height), at_x=cx), at_y=cy)
    anchors = {"top": (cx, m.x_height), "bottom": (cx, 0.0)}
    return _pack(c, m, anchors, turned)


def i_from_n(n_glyph: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    """``i``: the ``n`` stem plus a tittle."""
    c = ctx or n_glyph.context
    m = _n_record(n_glyph)
    stem = vertical_stem(c, 0.0, 0.0, m.x_height, width=m.stem)
    dot = tittle(c, m.stem / 2.0, m.x_height + m.stem * 0.55, size=m.stem * 0.95)
    return _pack(c, m, {"bottom": (m.stem / 2.0, 0.0)}, stem, dot)


def build_i(ctx: DesignContext, metrics: NMetrics | None = None) -> ComposedGlyph:
    """``i`` from the ``n`` stem (specimen helper and related form)."""
    return i_from_n(build_n(ctx, metrics), ctx)


def l_from_n(n_glyph: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    """``l``: the ``n`` stem rising to the ascender."""
    c = ctx or n_glyph.context
    m = _n_record(n_glyph)
    stem = vertical_stem(c, 0.0, 0.0, m.ascender, width=m.stem)
    anchors = {"top": (m.stem / 2.0, m.ascender), "bottom": (m.stem / 2.0, 0.0)}
    return _pack(c, m, anchors, stem)


# --- o family -----------------------------------------------------------------


def build_o(ctx: DesignContext, metrics: OMetrics | None = None) -> ComposedGlyph:
    """Control ``o``: superellipse bowl (continuous cubics) + counter."""
    m = metrics or o_metrics(ctx)
    cx, cy = m.rx, m.x_height / 2.0
    outer, hole = bowl(
        ctx, cx, cy, rx=m.rx, ry=m.ry, thickness=m.thickness, shape="superellipse", n=m.exponent
    )
    return (
        GlyphAssembler(ctx)
        .with_design(m)
        .add(outer)
        .add_hole(hole)
        .subtract_holes()
        .anchor("top", cx, m.x_height)
        .anchor("bottom", cx, 0.0)
        .build()
    )


def _cubic_pts(c: tuple[Point, Point, Point, Point]) -> Cubic:
    return (c[0].as_tuple(), c[1].as_tuple(), c[2].as_tuple(), c[3].as_tuple())


def _quarters(cx: float, cy: float, rx: float, ry: float, n: float) -> list[Cubic]:
    """Four CCW superellipse quadrants from ``+x`` as point tuples."""
    return [_cubic_pts(q) for q in superellipse_cubics(cx, cy, rx, ry, n)]


def _scale_x(c: Cubic, about: float, f: float) -> Cubic:
    return (
        (about + (c[0][0] - about) * f, c[0][1]),
        (about + (c[1][0] - about) * f, c[1][1]),
        (about + (c[2][0] - about) * f, c[2][1]),
        (about + (c[3][0] - about) * f, c[3][1]),
    )


def _bowl_stem_outline(
    o: OMetrics,
    stem: float,
    *,
    stem_bottom: float,
    stem_top: float,
    join: float,
) -> Outline:
    """``d``-type bowl (left) + stem (right) as two contours, outer CCW.

    The outer is the ``o`` bowl with its right side cut where it meets the
    stem's left face. The counter keeps the ``o`` counter's left half; its
    right half is stretched to the stem face so the counter has a straight
    inner stem, with the bowl ``join`` × its thickness where it meets it.
    """
    cx, cy = o.rx, o.x_height / 2.0
    s_r = cx + o.rx
    s_l = s_r - stem
    if s_l <= cx:
        raise ValueError("stem is wider than half the bowl; widen the o or thin the stem")

    q0, q1, q2, q3 = _quarters(cx, cy, o.rx, o.ry, o.exponent)
    top_cut = _split(q0, s_l, horizontal=False)
    bot_cut = _split(q3, s_l, horizontal=False)
    if top_cut is None or bot_cut is None:  # pragma: no cover - s_l inside bowl
        raise ValueError("stem face does not cross the bowl")
    y_t, y_b = top_cut[1][0][1], bot_cut[0][3][1]
    # Very bold stems meet the bowl beyond the stem ends; extend the stem.
    stem_top, stem_bottom = max(stem_top, y_t), min(stem_bottom, y_b)

    irx, iry = o.rx - o.thickness, o.ry - o.thickness
    iq0, iq1, iq2, iq3 = _quarters(cx, cy, irx, iry, o.exponent)
    flat = max(0.05, min(0.95, (y_t - join * o.thickness - cy) / iry))
    e = o.exponent
    q = 1.0 - (1.0 - flat**e) ** (1.0 / e)
    reach = (s_l - cx) / (1.0 - q)
    f = reach / irx
    i_top = _split(_scale_x(iq0, cx, f), s_l, horizontal=False)
    i_bot = _split(_scale_x(iq3, cx, f), s_l, horizontal=False)
    if i_top is None or i_bot is None:  # pragma: no cover - reach > s_l - cx
        raise ValueError("counter does not reach the stem face")

    b = PathBuilder()
    b.moveTo(s_r, stem_bottom)
    b.lineTo(s_r, stem_top)
    b.lineTo(s_l, stem_top)
    b.lineTo(*top_cut[1][0])
    _curve(b, top_cut[1])
    _curve(b, q1)
    _curve(b, q2)
    _curve(b, bot_cut[0])
    b.lineTo(s_l, stem_bottom)
    b.closePath()
    b.moveTo(*i_bot[0][3])
    b.lineTo(*i_top[1][0])
    _curve(b, i_top[1])
    _curve(b, iq1)
    _curve(b, iq2)
    _curve(b, i_bot[0])
    b.closePath()
    outer, counter = b.build().contours
    return Outline((outer, reverse_contour(counter)))


def _bowl_glyph(
    o_glyph: ComposedGlyph,
    n_glyph: ComposedGlyph | None,
    ctx: DesignContext | None,
    *,
    stem_left: bool,
    descends: bool,
    join: float,
) -> ComposedGlyph:
    c = ctx or o_glyph.context
    o = _o_record(o_glyph)
    stem = _n_record(n_glyph).stem if n_glyph is not None else o.thickness
    if descends:
        bottom, top = c.descender, o.x_height
    else:
        bottom, top = 0.0, (_n_record(n_glyph).ascender if n_glyph is not None else c.ascender)
    outline = _bowl_stem_outline(o, stem, stem_bottom=bottom, stem_top=top, join=join)
    cx = o.rx
    anchors = {"top": (cx, o.x_height)}
    if not descends:
        anchors["bottom"] = (cx, 0.0)
    if stem_left:
        outline = Outline(tuple(reverse_contour(k) for k in mirror_x(outline, at_x=o.rx).contours))
    return _pack(c, o, anchors, outline)


def d_from_o(
    o_glyph: ComposedGlyph,
    n_glyph: ComposedGlyph | None = None,
    ctx: DesignContext | None = None,
    *,
    join: float = 0.85,
) -> ComposedGlyph:
    """Derive ``d``: the ``o`` bowl with the ``n`` stem rising on the right.

    ``join`` is the bowl's thickness where it meets the stem, as a fraction of
    the ``o`` thickness (below 1 thins the junction, as designers do).
    """
    return _bowl_glyph(o_glyph, n_glyph, ctx, stem_left=False, descends=False, join=join)


def b_from_o(
    o_glyph: ComposedGlyph,
    n_glyph: ComposedGlyph | None = None,
    ctx: DesignContext | None = None,
    *,
    join: float = 0.85,
) -> ComposedGlyph:
    """Derive ``b``: mirror of ``d`` (stem on the left)."""
    return _bowl_glyph(o_glyph, n_glyph, ctx, stem_left=True, descends=False, join=join)


def q_from_o(
    o_glyph: ComposedGlyph,
    n_glyph: ComposedGlyph | None = None,
    ctx: DesignContext | None = None,
    *,
    join: float = 0.85,
) -> ComposedGlyph:
    """Derive ``q``: the ``o`` bowl with the stem descending on the right."""
    return _bowl_glyph(o_glyph, n_glyph, ctx, stem_left=False, descends=True, join=join)


def p_from_o(
    o_glyph: ComposedGlyph,
    n_glyph: ComposedGlyph | None = None,
    ctx: DesignContext | None = None,
    *,
    join: float = 0.85,
) -> ComposedGlyph:
    """Derive ``p``: mirror of ``q`` (stem descending on the left)."""
    return _bowl_glyph(o_glyph, n_glyph, ctx, stem_left=True, descends=True, join=join)


def a_from_o(
    o_glyph: ComposedGlyph,
    n_glyph: ComposedGlyph | None = None,
    ctx: DesignContext | None = None,
    *,
    join: float = 0.85,
) -> ComposedGlyph:
    """Derive single-storey ``a``: the ``o`` bowl with the stem at x-height."""
    c = ctx or o_glyph.context
    o = _o_record(o_glyph)
    stem = _n_record(n_glyph).stem if n_glyph is not None else o.thickness
    outline = _bowl_stem_outline(o, stem, stem_bottom=0.0, stem_top=o.x_height, join=join)
    anchors = {
        "top": (o.rx, o.x_height),
        "bottom": (o.rx, 0.0),
        "ogonek": (2.0 * o.rx - stem / 2.0, 0.0),
    }
    return _pack(c, o, anchors, outline)


def _rev(c: Cubic) -> Cubic:
    return (c[3], c[2], c[1], c[0])


def _ring(o: OMetrics) -> tuple[list[Cubic], list[Cubic]]:
    """Outer and counter quadrants of the ``o`` ring (CCW from ``+x``)."""
    cx, cy = o.rx, o.x_height / 2.0
    outer = _quarters(cx, cy, o.rx, o.ry, o.exponent)
    inner = _quarters(cx, cy, o.rx - o.thickness, o.ry - o.thickness, o.exponent)
    return outer, inner


def _terminal_x(o: OMetrics, aperture: float, closure: float) -> float:
    """Vertical terminal cut: opens toward the centre as ``aperture`` grows."""
    ap = max(0.0, min(1.0, aperture))
    return o.rx + (o.rx - o.thickness) * (0.95 - closure * ap)


def _cut(c: Cubic, where: float, *, horizontal: bool) -> tuple[Cubic, Cubic]:
    pieces = _split(c, where, horizontal=horizontal)
    if pieces is None:
        axis = "y" if horizontal else "x"
        raise ValueError(f"curve does not cross {axis}={where:.2f}; check o metrics")
    return pieces


def c_from_o(
    o_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    aperture: float | None = None,
) -> ComposedGlyph:
    """Derive ``c``: the ``o`` ring opened on the right with vertical terminals.

    ``aperture`` (default: the context's) moves both cuts toward the centre.
    One contour: outer arc, terminal, counter arc back, terminal.
    """
    c = ctx or o_glyph.context
    o = _o_record(o_glyph)
    (q0, q1, q2, q3), (i0, i1, i2, i3) = _ring(o)
    x_t = _terminal_x(o, c.aperture if aperture is None else aperture, 0.55)
    top = _cut(q0, x_t, horizontal=False)[1]
    bot = _cut(q3, x_t, horizontal=False)[0]
    itop = _cut(i0, x_t, horizontal=False)[1]
    ibot = _cut(i3, x_t, horizontal=False)[0]

    b = PathBuilder()
    b.moveTo(*top[0])
    for cubic in (top, q1, q2, bot):
        _curve(b, cubic)
    b.lineTo(*ibot[3])
    for cubic in (_rev(ibot), _rev(i2), _rev(i1), _rev(itop)):
        _curve(b, cubic)
    b.closePath()
    anchors = {"top": (o.rx, o.x_height), "bottom": (o.rx, 0.0)}
    return _pack(c, o, anchors, _ccw(b.build()))


def e_from_o(
    o_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    aperture: float | None = None,
    bar_raise: float = 0.25,
) -> ComposedGlyph:
    """Derive ``e``: the ``o`` ring with a crossbar and a lower aperture.

    The bar (``o`` thickness × context contrast) sits ``bar_raise`` × its
    thickness above the centre and runs from the inner left wall to the outer
    right edge. Below it the ring is cut at a vertical lower terminal, so the
    lower counter opens into the aperture. Two contours: outer and eye.
    """
    c = ctx or o_glyph.context
    o = _o_record(o_glyph)
    (q0, q1, q2, q3), (i0, i1, i2, i3) = _ring(o)
    cy = o.x_height / 2.0
    # Heavy weights thin the bar so it still fits inside the counter.
    room = 0.75 * (o.ry - o.thickness)
    bar_t = min(o.thickness * c.contrast, 1.2 * room)
    raise_ = max(-0.45, min(0.45, bar_raise)) * bar_t
    raise_ = max(-(room - bar_t / 2.0), min(room - bar_t / 2.0, raise_))
    bar_bot, bar_top = cy + raise_ - bar_t / 2.0, cy + raise_ + bar_t / 2.0
    x_t = _terminal_x(o, c.aperture if aperture is None else aperture, 0.45)

    below, right = _cut(q3, bar_bot, horizontal=True)
    lower = _cut(below, x_t, horizontal=False)[0]
    ilower = _cut(i3, x_t, horizontal=False)[0]
    iwall = _cut(i2, bar_bot, horizontal=True)[1]

    b = PathBuilder()
    b.moveTo(*right[0])
    for cubic in (right, q0, q1, q2, lower):
        _curve(b, cubic)
    b.lineTo(*ilower[3])
    _curve(b, _rev(ilower))
    _curve(b, _rev(iwall))
    b.closePath()

    eye_r = _cut(i0, bar_top, horizontal=True)[1]
    eye_l = _cut(i1, bar_top, horizontal=True)[0]
    b.moveTo(*eye_r[0])
    _curve(b, eye_r)
    _curve(b, eye_l)
    b.closePath()

    outer, eye = b.build().contours
    anchors = {"top": (o.rx, o.x_height), "bottom": (o.rx, 0.0)}
    return _pack(c, o, anchors, Outline((outer, reverse_contour(eye))))


def _from_controls(
    derive: Callable[[ComposedGlyph, ComposedGlyph | None], ComposedGlyph],
) -> Callable[[DesignContext], ComposedGlyph]:
    return lambda ctx: derive(build_o(ctx), build_n(ctx))


CONTROL_BUILDERS: dict[str, Callable[[DesignContext], ComposedGlyph]] = {
    "n": build_n,
    "h": build_h,
    "m": build_m,
    "r": build_r,
    "o": build_o,
    "u": build_u,
    "i": build_i,
    "l": lambda ctx: l_from_n(build_n(ctx)),
    "b": _from_controls(b_from_o),
    "d": _from_controls(d_from_o),
    "p": _from_controls(p_from_o),
    "q": _from_controls(q_from_o),
    "a": _from_controls(a_from_o),
    "c": lambda ctx: c_from_o(build_o(ctx)),
    "e": lambda ctx: e_from_o(build_o(ctx)),
}

def build_control_letter(ch: str, ctx: DesignContext) -> ComposedGlyph:
    key = ch.lower()
    try:
        return CONTROL_BUILDERS[key](ctx)
    except KeyError as exc:
        raise KeyError(
            f"no control/related builder for {ch!r}; have {sorted(CONTROL_BUILDERS)}"
        ) from exc


def build_control_word(text: str, ctx: DesignContext) -> list[ComposedGlyph]:
    return [build_control_letter(ch, ctx) for ch in text]

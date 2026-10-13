"""Capitals — control ``H`` and ``O``, and the forms that derive from them.

Capitals get their own design records: the cap stem is a touch heavier than
the lowercase stem (caps are bigger shapes and would otherwise look light
next to ``n``), and widths / crossbar height belong to the ``H``. Every
capital derives from the drawn ``H`` (stems, bars, width) and ``O`` (bowls)
the same way the lowercase derives from ``n`` and ``o``.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext
from typekernel.parts.control import (
    NMetrics,
    OMetrics,
    _ccw,
    _pack,
    build_o,
    n_metrics,
    o_metrics,
)

__all__ = [
    "E_from_H",
    "F_from_H",
    "HMetrics",
    "I_from_H",
    "L_from_H",
    "T_from_H",
    "build_H",
    "build_O",
    "cap_o_metrics",
    "h_cap_metrics",
]

Pt = tuple[float, float]

CAP_STEM_RATIO = 1.08
"""Cap stem over lowercase stem."""


@dataclass(frozen=True, slots=True)
class HMetrics:
    """Design record for the straight capitals (``H I L E F T`` …).

    Attributes:
        stem: Vertical cap stem.
        bar: Horizontal stroke thickness (crossbars, arms).
        cap_height: Flat top of the capitals.
        width: Ink width of ``H``, stem to stem.
        bar_y: Centre of the ``H`` crossbar (optically a little above centre).
        overshoot: Round / pointed capitals pass the zones by this much.
    """

    stem: float
    bar: float
    cap_height: float
    width: float
    bar_y: float
    overshoot: float

    def tuned(self, **kwargs: float) -> HMetrics:
        return replace(self, **kwargs)


def h_cap_metrics(ctx: DesignContext, n: NMetrics | None = None) -> HMetrics:
    """Derive the ``H`` record from family proportions and the ``n`` stem."""
    stem = (n or n_metrics(ctx)).stem * CAP_STEM_RATIO
    return HMetrics(
        stem=stem,
        bar=stem * ctx.contrast * 0.92,
        cap_height=ctx.cap_height,
        width=ctx.cap_height * (0.70 + 0.12 * ctx.aperture),
        bar_y=ctx.cap_height * 0.52,
        overshoot=ctx.overshoot,
    )


def cap_o_metrics(ctx: DesignContext, n: NMetrics | None = None) -> OMetrics:
    """The ``O`` record: the ``o`` construction at cap height with the cap stem."""
    lower = o_metrics(ctx)
    ry = ctx.cap_height / 2.0 + ctx.overshoot
    return OMetrics(
        rx=ry * (0.90 + 0.10 * ctx.aperture),
        ry=ry,
        thickness=(n or n_metrics(ctx)).stem * CAP_STEM_RATIO,
        exponent=lower.exponent,
        x_height=ctx.cap_height,
        overshoot=ctx.overshoot,
    )


def _h_record(glyph: ComposedGlyph) -> HMetrics:
    return glyph.design if isinstance(glyph.design, HMetrics) else h_cap_metrics(glyph.context)


def _polygon(points: list[Pt]) -> Outline:
    b = PathBuilder()
    b.moveTo(*points[0])
    for p in points[1:]:
        b.lineTo(*p)
    b.closePath()
    return _ccw(b.build())


def _cap_anchors(width: float, h: HMetrics) -> dict[str, Pt]:
    return {"top": (width / 2.0, h.cap_height), "bottom": (width / 2.0, 0.0)}


def build_H(ctx: DesignContext, metrics: HMetrics | None = None) -> ComposedGlyph:
    """Control ``H``: two cap stems and a crossbar, one contour."""
    h = metrics or h_cap_metrics(ctx)
    t, w, cap = h.stem, h.width, h.cap_height
    y0, y1 = h.bar_y - h.bar / 2.0, h.bar_y + h.bar / 2.0
    pts = [
        (0.0, 0.0),
        (t, 0.0),
        (t, y0),
        (w - t, y0),
        (w - t, 0.0),
        (w, 0.0),
        (w, cap),
        (w - t, cap),
        (w - t, y1),
        (t, y1),
        (t, cap),
        (0.0, cap),
    ]
    return _pack(ctx, h, _cap_anchors(w, h), _polygon(pts))


def build_O(ctx: DesignContext, metrics: OMetrics | None = None) -> ComposedGlyph:
    """Control ``O``: the ``o`` ring drawn at cap height with the cap stem."""
    return build_o(ctx, metrics or cap_o_metrics(ctx))


def I_from_H(H: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    """``I``: one ``H`` stem."""
    c = ctx or H.context
    h = _h_record(H)
    pts = [(0.0, 0.0), (h.stem, 0.0), (h.stem, h.cap_height), (0.0, h.cap_height)]
    return _pack(c, h, _cap_anchors(h.stem, h), _polygon(pts))


def L_from_H(
    H: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float = 0.78,
) -> ComposedGlyph:
    """``L``: the ``H`` stem with a foot ``width`` × the ``H`` width."""
    c = ctx or H.context
    h = _h_record(H)
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = width * h.width
    pts = [(0.0, 0.0), (w, 0.0), (w, bt), (t, bt), (t, cap), (0.0, cap)]
    return _pack(c, h, _cap_anchors(w, h), _polygon(pts))


def E_from_H(
    H: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float = 0.84,
) -> ComposedGlyph:
    """``E``: stem with three arms; the middle arm is shorter, the foot longest."""
    c = ctx or H.context
    h = _h_record(H)
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = width * h.width
    w_top, w_mid, w_bot = w * 0.97, w * 0.88, w
    m0, m1 = h.bar_y - bt / 2.0, h.bar_y + bt / 2.0
    pts = [
        (0.0, 0.0),
        (w_bot, 0.0),
        (w_bot, bt),
        (t, bt),
        (t, m0),
        (w_mid, m0),
        (w_mid, m1),
        (t, m1),
        (t, cap - bt),
        (w_top, cap - bt),
        (w_top, cap),
        (0.0, cap),
    ]
    return _pack(c, h, _cap_anchors(w, h), _polygon(pts))


def F_from_H(
    H: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float = 0.82,
) -> ComposedGlyph:
    """``F``: the ``E`` without its foot; the middle arm sits a little lower."""
    c = ctx or H.context
    h = _h_record(H)
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = width * h.width
    w_top, w_mid = w, w * 0.9
    mid = h.bar_y - 0.03 * cap
    m0, m1 = mid - bt / 2.0, mid + bt / 2.0
    pts = [
        (0.0, 0.0),
        (t, 0.0),
        (t, m0),
        (w_mid, m0),
        (w_mid, m1),
        (t, m1),
        (t, cap - bt),
        (w_top, cap - bt),
        (w_top, cap),
        (0.0, cap),
    ]
    return _pack(c, h, _cap_anchors(w, h), _polygon(pts))


def T_from_H(
    H: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float = 0.92,
) -> ComposedGlyph:
    """``T``: an ``H`` stem centred under a top bar ``width`` × the ``H`` width."""
    c = ctx or H.context
    h = _h_record(H)
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = width * h.width
    s0, s1 = (w - t) / 2.0, (w + t) / 2.0
    pts = [
        (s0, 0.0),
        (s1, 0.0),
        (s1, cap - bt),
        (w, cap - bt),
        (w, cap),
        (0.0, cap),
        (0.0, cap - bt),
        (s0, cap - bt),
    ]
    return _pack(c, h, _cap_anchors(w, h), _polygon(pts))

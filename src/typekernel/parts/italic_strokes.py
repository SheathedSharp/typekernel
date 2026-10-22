"""Standalone italic writing strokes for Usage A self-compose.

These are the public lifts of the private emitters formerly buried in
``parts.control``. Agents draw continuous outlines with the ``emit_*`` helpers,
or take closed Outline parts (``italic_entry_kick``, ``italic_exit_outstroke``,
``italic_written_stem``) and compose via :func:`~typekernel.parts.compose.soft_union`
/ :class:`~typekernel.parts.compose.GlyphAssembler`.

Not oblique shear. Not a DesignSequence / Controls path.
"""

from __future__ import annotations

from typekernel.geo.contour import reverse_contour, signed_area
from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.parts.context import DesignContext

__all__ = [
    "emit_italic_entry_kick",
    "emit_italic_exit_outstroke",
    "italic_entry_kick",
    "italic_exit_outstroke",
    "italic_kick_dims",
    "italic_written_stem",
]


def italic_kick_dims(stem: float) -> tuple[float, float]:
    """``(dx, dy)`` for written entry kick / exit outstroke foot cuts.

    Sized from stem so ``wght`` masters keep a fixed segment recipe.
    """
    dx = max(2.5, stem * 0.18)
    dy = max(3.5, stem * 0.32)
    return dx, dy


def emit_italic_entry_kick(
    b: PathBuilder,
    l0: float,
    *,
    stem: float,
    left_top: float,
    y0: float = 0.0,
) -> None:
    """Entry kick into the left stem face (written lead-in).

    Issues ``moveTo``: starts inset at ``y0``, cubic into ``(l0, y0+dy)``,
    then rises to ``left_top``. ``y0`` is the descender floor for italic ``f``.
    """
    dx, dy = italic_kick_dims(stem)
    rise = max(2.0, left_top - y0)
    dy = min(dy, max(2.0, rise * 0.22))
    b.moveTo(l0 + dx, y0)
    b.curveTo(l0 + dx * 0.35, y0, l0, y0 + dy * 0.45, l0, y0 + dy)
    b.lineTo(l0, left_top)


def emit_italic_exit_outstroke(
    b: PathBuilder,
    r0: float,
    r1: float,
    *,
    stem: float,
) -> None:
    """Outer-right baseline outstroke (written exit), then across to ``r0``.

    Current point must lie on ``x=r1`` with ``y > 0``. Replaces a sharp
    ``lineTo(r1, 0)`` + ``lineTo(r0, 0)`` foot corner.
    """
    dx, dy = italic_kick_dims(stem)
    b.lineTo(r1, dy)
    b.curveTo(r1, dy * 0.45, r1 - dx * 0.35, 0.0, r1 - dx, 0.0)
    b.lineTo(r0, 0.0)


def _ccw(outline: Outline) -> Outline:
    c0 = outline.contours[0]
    if signed_area(c0) < 0:
        return Outline((reverse_contour(c0),))
    return outline


def italic_entry_kick(
    ctx: DesignContext,
    x_left: float,
    *,
    stem: float | None = None,
    left_top: float | None = None,
    y0: float = 0.0,
) -> Outline:
    """Closed left-stem outline with written entry kick (no exit cut).

    ``x_left`` is the outer left face. Top is flat; baseline carries the kick.
    Prefer :func:`italic_written_stem` when both entry and exit are wanted.
    """
    t = ctx.stem if stem is None else stem
    if t <= 0:
        raise ValueError(f"stem must be positive, got {t!r}")
    top = ctx.x_height if left_top is None else left_top
    dx, dy = italic_kick_dims(t)
    dy = min(dy, max(2.0, (top - y0) * 0.22))
    b = PathBuilder()
    emit_italic_entry_kick(b, x_left, stem=t, left_top=top, y0=y0)
    b.lineTo(x_left + t, top)
    b.lineTo(x_left + t, y0)
    b.lineTo(x_left + dx, y0)
    b.closePath()
    return _ccw(b.build())


def italic_exit_outstroke(
    ctx: DesignContext,
    x_inner: float,
    x_outer: float,
    *,
    stem: float | None = None,
    top: float | None = None,
) -> Outline:
    """Closed right-stem outline with written baseline outstroke.

    ``x_inner`` / ``x_outer`` are the inner and outer faces of the right stem
    (``x_outer > x_inner``). Top is flat.
    """
    t = ctx.stem if stem is None else stem
    if t <= 0:
        raise ValueError(f"stem must be positive, got {t!r}")
    if x_outer <= x_inner:
        raise ValueError("x_outer must be > x_inner")
    stem_top = ctx.x_height if top is None else top
    b = PathBuilder()
    b.moveTo(x_inner, stem_top)
    b.lineTo(x_outer, stem_top)
    emit_italic_exit_outstroke(b, x_inner, x_outer, stem=t)
    b.lineTo(x_inner, stem_top)
    b.closePath()
    return _ccw(b.build())


def italic_written_stem(
    ctx: DesignContext,
    x_left: float = 0.0,
    *,
    stem: float | None = None,
    top: float | None = None,
    contrast_inset: bool = True,
) -> Outline:
    """Single vertical stem with entry kick + exit outstroke (sans italic).

    Matches the former private ``_italic_single_stem_outline`` recipe used by
    ``i``/``l`` under construct slant. ``contrast_inset`` thins the top face
    when ``ctx.contrast < 1``.
    """
    t = ctx.stem if stem is None else stem
    if t <= 0:
        raise ValueError(f"stem must be positive, got {t!r}")
    stem_top = ctx.x_height if top is None else top
    dx, dy = italic_kick_dims(t)
    dy = min(dy, max(2.0, stem_top * 0.12))
    inset = 0.0
    if contrast_inset and abs(ctx.contrast - 1.0) >= 1e-9:
        inset = (t - t * ctx.contrast) / 2.0
    b = PathBuilder()
    b.moveTo(x_left + dx, 0.0)
    b.curveTo(x_left + dx * 0.35, 0.0, x_left, dy * 0.45, x_left, dy)
    b.lineTo(x_left + inset, stem_top)
    b.lineTo(x_left + t - inset, stem_top)
    b.lineTo(x_left + t, dy)
    b.curveTo(
        x_left + t,
        dy * 0.45,
        x_left + t - dx * 0.35,
        0.0,
        x_left + t - dx,
        0.0,
    )
    b.closePath()
    return _ccw(b.build())

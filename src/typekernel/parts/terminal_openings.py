"""Map ``DesignContext.terminal_style`` to opening geometry knobs."""

from __future__ import annotations

import importlib.util
from typing import Literal

from typekernel.geo.outline import Outline, bounds
from typekernel.parts.context import DesignContext

__all__ = [
    "apply_terminal_shear",
    "opening_closure",
    "r_arm_scale",
    "s_opening_factor",
]

_BALL_RADIUS_RATIO = 0.36


def opening_closure(ctx: DesignContext, vertical_closure: float) -> float:
    """Closure scalar for bowl / aperture cuts (larger → more open)."""
    style = ctx.terminal_style
    if style == "vertical":
        return vertical_closure
    if style == "horizontal":
        return vertical_closure * 0.7647058823529411  # 0.42 / 0.55
    if style == "angled":
        return vertical_closure * 0.88
    if style == "ball":
        return vertical_closure * 0.92
    if style == "flared":
        return vertical_closure * 0.82
    return vertical_closure


def s_opening_factor(ctx: DesignContext, aperture: float) -> float:
    """Right/left opening reach for ``s`` (mirrors ``c`` closure behaviour)."""
    base = 0.95 - 0.5 * max(0.0, min(1.0, aperture))
    style = ctx.terminal_style
    if style == "vertical":
        return base
    if style == "horizontal":
        return base + 0.08
    if style == "angled":
        return base + 0.04
    if style == "ball":
        return base + 0.02
    if style == "flared":
        return base + 0.06
    return base


def r_arm_scale(ctx: DesignContext) -> float:
    """Scale ``r`` / ``R`` terminal position along the shoulder."""
    style = ctx.terminal_style
    if style == "vertical":
        return 1.0
    if style == "horizontal":
        return 0.86
    if style == "angled":
        return 0.93
    if style == "ball":
        return 0.96
    if style == "flared":
        return 0.90
    return 1.0


def _shear_angle_deg(ctx: DesignContext) -> float:
    style = ctx.terminal_style
    if style == "horizontal":
        return -10.0
    if style == "angled":
        return -16.0
    if style == "flared":
        return 18.0
    return 0.0


def _ball_terminal(
    ctx: DesignContext,
    outline: Outline,
    at: tuple[float, float],
    *,
    ball_radius: float | None = None,
) -> Outline:
    if importlib.util.find_spec("pathops") is None:
        return outline
    from typekernel.parts.terminals import ball_end

    radius = ball_radius
    if radius is None:
        radius = max(4.0, ctx.stem * _BALL_RADIUS_RATIO)
    return ball_end(outline, at, radius=radius, ctx=ctx)


def _tip_cut(
    ctx: DesignContext,
    outline: Outline,
    at: tuple[float, float],
    *,
    prefer_flat: bool = False,
    along: Literal["x", "y"] = "y",
    inward: Literal["auto", "+", "-"] = "-",
    band: float | None = None,
    ball_radius: float | None = None,
) -> Outline:
    if ctx.terminal_style == "ball":
        return _ball_terminal(ctx, outline, at, ball_radius=ball_radius)
    shear_band = band if band is not None else max(6.0, ctx.stem * 0.38)
    use_flat = ctx.terminal_style == "horizontal" or (
        ctx.terminal_style == "angled" and prefer_flat
    )
    if use_flat and importlib.util.find_spec("pathops") is not None:
        from typekernel.parts.terminals import flat_end

        return flat_end(
            outline,
            at,
            angle_deg=90.0,
            length=ctx.stem * 3.0,
            kerf=max(2.0, ctx.stem * 0.22),
            keep="negative",
        )
    from typekernel.parts.terminals import shear_end

    angle = _shear_angle_deg(ctx)
    return shear_end(
        outline, at, angle, band=shear_band, along=along, inward=inward
    )


def apply_terminal_shear(
    ctx: DesignContext,
    outline: Outline,
    *,
    at: tuple[float, float] | None = None,
    prefer_flat: bool = False,
    along: Literal["x", "y"] = "y",
    inward: Literal["auto", "+", "-"] = "-",
    band: float | None = None,
    ball_radius: float | None = None,
) -> Outline:
    """Shear, flat-cut, ball, or flare one open terminal on ``outline``."""
    if ctx.terminal_style == "vertical":
        return outline
    if at is None:
        try:
            _min_x, _min_y, max_x, max_y = bounds(outline)
        except ValueError:
            return outline
        at = (max_x, max_y - ctx.stem * 0.12)
    return _tip_cut(
        ctx,
        outline,
        at,
        prefer_flat=prefer_flat,
        along=along,
        inward=inward,
        band=band,
        ball_radius=ball_radius,
    )

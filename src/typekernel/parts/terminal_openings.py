"""Map ``DesignContext.terminal_style`` to opening geometry knobs."""

from __future__ import annotations

from typekernel.geo.outline import Outline, bounds
from typekernel.parts.context import DesignContext

__all__ = [
    "apply_terminal_shear",
    "opening_closure",
    "r_arm_scale",
    "s_opening_factor",
]


def opening_closure(ctx: DesignContext, vertical_closure: float) -> float:
    """Closure scalar for bowl / aperture cuts (larger → more open)."""
    if ctx.terminal_style == "vertical":
        return vertical_closure
    if ctx.terminal_style == "horizontal":
        return vertical_closure * 0.7647058823529411  # 0.42 / 0.55
    return vertical_closure * 0.88


def s_opening_factor(ctx: DesignContext, aperture: float) -> float:
    """Right/left opening reach for ``s`` (mirrors ``c`` closure behaviour)."""
    base = 0.95 - 0.5 * max(0.0, min(1.0, aperture))
    if ctx.terminal_style == "vertical":
        return base
    if ctx.terminal_style == "horizontal":
        return base + 0.08
    return base + 0.04


def r_arm_scale(ctx: DesignContext) -> float:
    """Scale ``r`` / ``R`` terminal position along the shoulder."""
    if ctx.terminal_style == "vertical":
        return 1.0
    if ctx.terminal_style == "horizontal":
        return 0.86
    return 0.93


def _tip_cut(ctx: DesignContext, outline: Outline, at: tuple[float, float]) -> Outline:
    band = max(6.0, ctx.stem * 0.38)
    if ctx.terminal_style == "horizontal":
        import importlib.util

        if importlib.util.find_spec("pathops") is not None:
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

    angle = -10.0 if ctx.terminal_style == "horizontal" else -16.0
    return shear_end(outline, at, angle, band=band, along="y", inward="-")


def apply_terminal_shear(
    ctx: DesignContext,
    outline: Outline,
    *,
    at: tuple[float, float] | None = None,
) -> Outline:
    """Shear or flat-cut one open terminal on ``outline``."""
    if ctx.terminal_style == "vertical":
        return outline
    if at is None:
        try:
            _min_x, _min_y, max_x, max_y = bounds(outline)
        except ValueError:
            return outline
        at = (max_x, max_y - ctx.stem * 0.12)
    return _tip_cut(ctx, outline, at)

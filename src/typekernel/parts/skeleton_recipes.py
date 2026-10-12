"""Compatibility letter entry points — prefer :mod:`typekernel.parts.control`.

``skel_n`` / ``skel_h`` / ``skel_o`` / ``skel_u`` / ``skel_i`` delegate to the
control-glyph layer (continuous outlines + related forms). Kept so older
callers and the specimen script keep working without CAD boolean troughs.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

from typekernel.parts.compose import ComposedGlyph, GlyphAssembler
from typekernel.parts.context import DesignContext
from typekernel.parts.control import (
    build_h,
    build_i,
    build_n,
    build_o,
    build_u,
)
from typekernel.parts.primitives import vertical_stem
from typekernel.parts.skeleton import Skeleton, Stroke

__all__ = [
    "SKEL_BUILDERS",
    "build_skel_letter",
    "build_skel_word",
    "skel_c",
    "skel_h",
    "skel_i",
    "skel_l",
    "skel_n",
    "skel_o",
    "skel_u",
    "skeleton_c",
    "skeleton_h",
    "skeleton_i",
    "skeleton_l",
    "skeleton_n",
    "skeleton_o",
    "skeleton_u",
]


def _counter_width(ctx: DesignContext) -> float:
    return ctx.x_height * (0.46 + 0.12 * ctx.aperture)


def _shallow_shear_deg(ctx: DesignContext) -> float:
    return 4.0 + 4.0 * ctx.aperture


# --- stroke-graph sketches (metrics / docs only) ----------------------------


def skeleton_l(ctx: DesignContext) -> Skeleton:
    return Skeleton.of(Stroke.from_points("stem", [(0.0, 0.0), (0.0, ctx.ascender)]))


def skeleton_i(ctx: DesignContext) -> Skeleton:
    top = ctx.x_height
    cy = top + ctx.stem * 0.85
    return Skeleton.of(
        Stroke.from_points("stem", [(0.0, 0.0), (0.0, top)]),
        Stroke.from_points("tittle", [(0.0, cy), (0.0, cy + 1.0)]),
    )


def skeleton_n(ctx: DesignContext) -> Skeleton:
    w = _counter_width(ctx)
    top = ctx.x_height + ctx.overshoot
    return Skeleton.of(
        Stroke.from_points("left", [(0.0, 0.0), (0.0, top)]),
        Stroke.from_points("arch", [(0.0, top * 0.55), (w / 2.0, top), (w, top * 0.55)]),
        Stroke.from_points("right", [(w, top * 0.55), (w, 0.0)]),
    )


def skeleton_h(ctx: DesignContext) -> Skeleton:
    w = _counter_width(ctx)
    top = ctx.x_height + ctx.overshoot
    return Skeleton.of(
        Stroke.from_points("left", [(0.0, 0.0), (0.0, ctx.ascender)]),
        Stroke.from_points("arch", [(0.0, top * 0.55), (w / 2.0, top), (w, top * 0.55)]),
        Stroke.from_points("right", [(w, top * 0.55), (w, 0.0)]),
    )


def skeleton_o(ctx: DesignContext) -> Skeleton:
    ry = ctx.x_height / 2.0 + ctx.overshoot
    rx = ry * (0.88 + 0.10 * ctx.aperture)
    return Skeleton.of(
        Stroke.from_points(
            "ring",
            [(rx, 0.0), (2 * rx, ry), (rx, 2 * ry), (0.0, ry)],
            closed=True,
        )
    )


def skeleton_c(ctx: DesignContext) -> Skeleton:
    ry = ctx.x_height / 2.0 + ctx.overshoot
    rx = ry * (0.88 + 0.10 * ctx.aperture)
    return Skeleton.of(
        Stroke.from_points(
            "bowl",
            [
                (rx * 1.6, ry * 0.25),
                (rx, 0.0),
                (0.0, ry),
                (rx, 2 * ry),
                (rx * 1.6, ry * 1.75),
            ],
        )
    )


def skeleton_u(ctx: DesignContext) -> Skeleton:
    w = _counter_width(ctx)
    return Skeleton.of(
        Stroke.from_points("left", [(0.0, ctx.x_height), (0.0, w * 0.3)]),
        Stroke.from_points(
            "bottom", [(0.0, w * 0.3), (w / 2.0, -ctx.overshoot), (w, w * 0.3)]
        ),
        Stroke.from_points("right", [(w, w * 0.3), (w, ctx.x_height)]),
    )


# --- builders ---------------------------------------------------------------


def skel_l(ctx: DesignContext, **opts: object) -> ComposedGlyph:
    del opts
    return GlyphAssembler(ctx).add(vertical_stem(ctx, 0.0, 0.0, ctx.ascender)).build()


def skel_i(ctx: DesignContext, **opts: object) -> ComposedGlyph:
    del opts
    return build_i(ctx)


def skel_n(ctx: DesignContext, **opts: object) -> ComposedGlyph:
    del opts
    return build_n(ctx)


def skel_h(ctx: DesignContext, **opts: object) -> ComposedGlyph:
    del opts
    return build_h(ctx)


def skel_o(ctx: DesignContext, **opts: object) -> ComposedGlyph:
    del opts
    return build_o(ctx)


def skel_u(ctx: DesignContext, **opts: object) -> ComposedGlyph:
    del opts
    return build_u(ctx)


def skel_c(ctx: DesignContext, **opts: object) -> ComposedGlyph:
    """Open bowl with shallow shear (not yet on the control/derive chain)."""
    del opts
    from typekernel.parts.aperture import open_bowl_ring
    from typekernel.parts.primitives import bowl
    from typekernel.parts.terminals import shear_end

    ry = ctx.x_height / 2.0 + ctx.overshoot
    rx = ry * (0.88 + 0.10 * ctx.aperture)
    n_exp = 2.0 + 0.7 * (1.0 - max(0.0, min(1.0, ctx.roundness)))
    outer, hole = bowl(
        ctx,
        rx,
        ctx.x_height / 2.0,
        rx=rx,
        ry=ry,
        thickness=ctx.stem,
        shape="superellipse",
        n=n_exp,
    )
    amount = rx * (0.22 + 0.28 * ctx.aperture)
    opened = open_bowl_ring(outer, hole, "right", amount, ctx)
    shear = _shallow_shear_deg(ctx)
    y_hi = ctx.x_height / 2.0 + ry * 0.55
    y_lo = ctx.x_height / 2.0 - ry * 0.55
    opened = shear_end(
        opened, (rx * 1.85, y_hi), shear, along="x", band=ctx.stem * 0.9
    )
    opened = shear_end(
        opened, (rx * 1.85, y_lo), -shear, along="x", band=ctx.stem * 0.9
    )
    return GlyphAssembler(ctx).add(opened).build()


SKEL_BUILDERS: Mapping[str, Callable[..., ComposedGlyph]] = {
    "l": skel_l,
    "i": skel_i,
    "n": skel_n,
    "h": skel_h,
    "o": skel_o,
    "c": skel_c,
    "u": skel_u,
}


def build_skel_letter(ch: str, ctx: DesignContext, **opts: object) -> ComposedGlyph:
    key = ch.lower()
    try:
        return SKEL_BUILDERS[key](ctx, **opts)
    except KeyError as exc:
        raise KeyError(
            f"no skeleton recipe for {ch!r}; have {sorted(SKEL_BUILDERS)}"
        ) from exc


def build_skel_word(text: str, ctx: DesignContext, **opts: object) -> list[ComposedGlyph]:
    return [build_skel_letter(ch, ctx, **opts) for ch in text]

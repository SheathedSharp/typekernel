"""Parameterised skeleton letter recipes (shape-agnostic, context-driven).

Letters are stroke graphs sized from :class:`~typekernel.parts.context.DesignContext`
(``x_height``, ``stem``, ``aperture``, ``overshoot``, ``roundness``, …). No
face-specific beauty hacks — the same builders serve paper and coding presets.

Construction path: :class:`~typekernel.parts.skeleton.Skeleton` →
:func:`~typekernel.parts.skeleton.trace_letter` (pen expand, optional terminals,
union, blend, ease).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping

from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext
from typekernel.parts.skeleton import EndTreatment, Skeleton, Stroke, trace_letter

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


def _arc(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    a0_deg: float,
    a1_deg: float,
    *,
    n: int = 14,
) -> list[tuple[float, float]]:
    """Polyline samples along an elliptical arc (degrees, CCW)."""
    if n < 2:
        raise ValueError("arc needs n >= 2")
    a0 = math.radians(a0_deg)
    a1 = math.radians(a1_deg)
    # unwrap so we always go CCW from a0 toward a1
    da = a1 - a0
    while da <= 0:
        da += 2 * math.pi
    return [
        (
            cx + rx * math.cos(a0 + da * i / n),
            cy + ry * math.sin(a0 + da * i / n),
        )
        for i in range(n + 1)
    ]


def _counter_width(ctx: DesignContext) -> float:
    """Inner counter width between stem centerlines."""
    return ctx.x_height * (0.46 + 0.12 * ctx.aperture)


def _trace(
    skeleton: Skeleton,
    ctx: DesignContext,
    *,
    union: bool = True,
    blend: bool | float = True,
    ease: bool = False,
    join: str = "round",
    cap: str = "round",
) -> ComposedGlyph:
    return trace_letter(
        skeleton,
        ctx,
        union=union,
        blend=blend,
        ease=ease,
        join=join,  # type: ignore[arg-type]
        cap=cap,  # type: ignore[arg-type]
    )


# --- skeletons (pure geometry) ----------------------------------------------


def skeleton_l(ctx: DesignContext) -> Skeleton:
    """Single vertical stem to ascender."""
    return Skeleton.of(
        Stroke.from_points("stem", [(0.0, 0.0), (0.0, ctx.ascender)])
    )


def skeleton_i(ctx: DesignContext) -> Skeleton:
    """Stem to x-height + filled tittle (short stroke, round caps)."""
    top = ctx.x_height
    r = ctx.stem * 0.42
    cy = top + ctx.stem * 0.75 + r
    # Tiny segment + round caps ≈ disk (closed ring would leave a counter).
    return Skeleton.of(
        Stroke.from_points("stem", [(0.0, 0.0), (0.0, top)]),
        Stroke.from_points(
            "tittle",
            [(0.0, cy - 0.5), (0.0, cy + 0.5)],
            thickness=2.0 * r,
            cap="round",
        ),
    )


def skeleton_n(ctx: DesignContext) -> Skeleton:
    """Left stem + arch + right stem (centerlines from aperture)."""
    w = _counter_width(ctx)
    top = ctx.x_height
    ry = w * 0.55 + ctx.overshoot * 0.5
    cy = top - ry
    arch = _arc(w / 2.0, cy, w / 2.0, ry, 180.0, 0.0, n=12)
    # Start arch at left stem; end drops into right stem.
    left = [(0.0, 0.0), (0.0, top)]
    right = [(w, arch[-1][1]), (w, 0.0)]
    return Skeleton.of(
        Stroke.from_points("left", left),
        Stroke.from_points("arch", arch),
        Stroke.from_points("right", right),
    )


def skeleton_h(ctx: DesignContext) -> Skeleton:
    """Ascender left stem + n-like arch and right stem."""
    w = _counter_width(ctx)
    top = ctx.x_height
    ry = w * 0.55 + ctx.overshoot * 0.5
    cy = top - ry
    arch = _arc(w / 2.0, cy, w / 2.0, ry, 180.0, 0.0, n=12)
    left = [(0.0, 0.0), (0.0, ctx.ascender)]
    right = [(w, arch[-1][1]), (w, 0.0)]
    return Skeleton.of(
        Stroke.from_points("left", left),
        Stroke.from_points("arch", arch),
        Stroke.from_points("right", right),
    )


def skeleton_o(ctx: DesignContext) -> Skeleton:
    """Closed elliptical ring; rx grows with aperture, ry with overshoot."""
    ry = ctx.x_height / 2.0 + ctx.overshoot
    rx = ry * (0.82 + 0.14 * ctx.aperture)
    cy = ctx.x_height / 2.0
    pts = _arc(rx, cy, rx, ry, 0.0, 360.0, n=16)[:-1]
    return Skeleton.of(Stroke.from_points("ring", pts, closed=True))


def skeleton_c(ctx: DesignContext) -> Skeleton:
    """Open bowl arc; aperture widens the mouth (smaller sweep gap)."""
    ry = ctx.x_height / 2.0 + ctx.overshoot
    rx = ry * (0.82 + 0.14 * ctx.aperture)
    cy = ctx.x_height / 2.0
    # Mouth opening scales with aperture (degrees left un-drawn on the right).
    gap = 55.0 + 50.0 * (1.0 - ctx.aperture)
    a0 = gap / 2.0
    a1 = 360.0 - gap / 2.0
    pts = _arc(rx, cy, rx, ry, a0, a1, n=16)
    shear = 10.0 + 8.0 * ctx.aperture
    return Skeleton.of(
        Stroke.from_points(
            "bowl",
            pts,
            start=EndTreatment("shear", angle_deg=-shear),
            end=EndTreatment("shear", angle_deg=shear),
            cap="butt",
        )
    )


def skeleton_u(ctx: DesignContext) -> Skeleton:
    """U-trough: left stem, bottom arc, right stem."""
    w = _counter_width(ctx)
    top = ctx.x_height
    ry = w * 0.50 + ctx.overshoot
    cy = ry
    bottom = _arc(w / 2.0, cy, w / 2.0, ry, 180.0, 360.0, n=12)
    left = [(0.0, top), (0.0, bottom[0][1])]
    right = [(w, bottom[-1][1]), (w, top)]
    return Skeleton.of(
        Stroke.from_points("left", left),
        Stroke.from_points("bottom", bottom),
        Stroke.from_points("right", right),
    )


# --- traced letters ---------------------------------------------------------


def skel_l(ctx: DesignContext, **opts: object) -> ComposedGlyph:
    return _trace(skeleton_l(ctx), ctx, **opts)  # type: ignore[arg-type]


def skel_i(ctx: DesignContext, **opts: object) -> ComposedGlyph:
    # Stem and tittle are disjoint; round-cap pathops union is unreliable on
    # separated components — keep both solids (bounds/advance still correct).
    opts = dict(opts)
    opts.setdefault("union", False)
    return _trace(skeleton_i(ctx), ctx, **opts)  # type: ignore[arg-type]


def skel_n(ctx: DesignContext, **opts: object) -> ComposedGlyph:
    return _trace(skeleton_n(ctx), ctx, **opts)  # type: ignore[arg-type]


def skel_h(ctx: DesignContext, **opts: object) -> ComposedGlyph:
    return _trace(skeleton_h(ctx), ctx, **opts)  # type: ignore[arg-type]


def skel_o(ctx: DesignContext, **opts: object) -> ComposedGlyph:
    return _trace(skeleton_o(ctx), ctx, **opts)  # type: ignore[arg-type]


def skel_c(ctx: DesignContext, **opts: object) -> ComposedGlyph:
    return _trace(skeleton_c(ctx), ctx, **opts)  # type: ignore[arg-type]


def skel_u(ctx: DesignContext, **opts: object) -> ComposedGlyph:
    return _trace(skeleton_u(ctx), ctx, **opts)  # type: ignore[arg-type]


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
    """Trace one lowercase skeleton letter; ``KeyError`` if unsupported."""
    key = ch.lower()
    try:
        builder = SKEL_BUILDERS[key]
    except KeyError as exc:
        raise KeyError(
            f"no skeleton recipe for {ch!r}; have {sorted(SKEL_BUILDERS)}"
        ) from exc
    return builder(ctx, **opts)


def build_skel_word(
    text: str,
    ctx: DesignContext,
    **opts: object,
) -> list[ComposedGlyph]:
    """Trace each character with the shared context (same opts for all)."""
    return [build_skel_letter(ch, ctx, **opts) for ch in text]

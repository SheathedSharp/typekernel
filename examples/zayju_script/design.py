"""Florid English letter-writing script — hand-built stroke topologies.

Brief phrase: ``zayju Discover everywhere``.

This is **not** a slanted humanist sans. Each glyph is a calligraphy skeleton
(oval / stem / entry-exit) expanded with a contrast broad-nib :class:`Pen`
via :func:`~typekernel.parts.skeleton.trace_letter`. Slant lives in the
centerline coordinates (shear while drawing), not in ``oblique_font``.

Charset (case-sensitive for the brief)::

    a c d e h i j o r s u v w y z D  + space
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Final

from typekernel.geo.stroke import CubicBezier
from typekernel.parts import (
    ComposedGlyph,
    DesignContext,
    Skeleton,
    Stroke,
    trace_letter,
)

# ---------------------------------------------------------------------------
# Voice metrics (script proportions — documented deltas from display preset)
# ---------------------------------------------------------------------------
SLANT_DEG: Final = 28.0
SHEAR: Final = math.tan(math.radians(SLANT_DEG))
K: Final = 0.5523

# Broad nib: thick on near-vertical downs, thin on horizontal connectors.
NIB_THICKNESS: Final = 48.0
NIB_CONTRAST: Final = 0.28
NIB_ANGLE: Final = 52.0  # degrees — classic pointed-pen / roundhand bias

X_HEIGHT: Final = 420.0
CAP_HEIGHT: Final = 700.0
ASCENDER: Final = 780.0
DESCENDER: Final = -300.0


def script_context() -> DesignContext:
    """Base metrics for packing; topology comes from skeletons, not Controls."""
    return DesignContext.display().tuned(
        stem=NIB_THICKNESS,
        x_height=X_HEIGHT,
        cap_height=CAP_HEIGHT,
        ascender=ASCENDER,
        descender=DESCENDER,
        overshoot=14.0,
        sidebearing_ratio=0.05,
        contrast=NIB_CONTRAST,
        roundness=0.22,
        aperture=0.55,
    )


def _S(x: float, y: float) -> tuple[float, float]:
    """Bake writing slant into the skeleton (not a post-export shear)."""
    return (x + y * SHEAR, y)


def _C(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
) -> CubicBezier:
    return CubicBezier(_S(*p0), _S(*p1), _S(*p2), _S(*p3))


def _ellipse(
    cx: float, cy: float, rx: float, ry: float
) -> tuple[CubicBezier, CubicBezier, CubicBezier, CubicBezier]:
    """Closed upright oval in design space; slant applied per control point."""
    return (
        _C((cx + rx, cy), (cx + rx, cy + K * ry), (cx + K * rx, cy + ry), (cx, cy + ry)),
        _C((cx, cy + ry), (cx - K * rx, cy + ry), (cx - rx, cy + K * ry), (cx - rx, cy)),
        _C((cx - rx, cy), (cx - rx, cy - K * ry), (cx - K * rx, cy - ry), (cx, cy - ry)),
        _C((cx, cy - ry), (cx + K * rx, cy - ry), (cx + rx, cy - K * ry), (cx + rx, cy)),
    )


def _stroke(
    name: str,
    segs: tuple[CubicBezier, ...] | list[CubicBezier],
    *,
    closed: bool = False,
    thickness: float | None = None,
) -> Stroke:
    return Stroke.from_beziers(
        name,
        tuple(segs),
        closed=closed,
        thickness=thickness if thickness is not None else NIB_THICKNESS,
        contrast=NIB_CONTRAST,
        angle_deg=NIB_ANGLE,
        join="round",
        cap="round",
    )


def _poly(
    name: str,
    pts: list[tuple[float, float]],
    *,
    closed: bool = False,
    thickness: float | None = None,
) -> Stroke:
    return Stroke.from_points(
        name,
        [_S(*p) for p in pts],
        closed=closed,
        thickness=thickness if thickness is not None else NIB_THICKNESS,
        contrast=NIB_CONTRAST,
        angle_deg=NIB_ANGLE,
        join="round",
        cap="round",
    )


def _trace(*strokes: Stroke, ctx: DesignContext | None = None) -> ComposedGlyph:
    return trace_letter(
        Skeleton.of(*strokes),
        ctx or script_context(),
        union=True,
        blend=True,
        ease=False,
        join="round",
        cap="round",
    )


# ---------------------------------------------------------------------------
# Glyph builders — cursive / semi-connected roundhand skeletons
# ---------------------------------------------------------------------------


def glyph_o(ctx: DesignContext | None = None) -> ComposedGlyph:
    return _trace(_stroke("ring", _ellipse(175, 210, 100, 200), closed=True), ctx=ctx)


def glyph_a(ctx: DesignContext | None = None) -> ComposedGlyph:
    ring = _stroke("ring", _ellipse(155, 210, 92, 195), closed=True)
    # Right stem with exit flourish toward next letter.
    stem = _poly(
        "stem",
        [(230, 380), (245, 220), (255, 40), (300, 12), (370, 55), (400, 90)],
    )
    entry = _poly("entry", [(20, 100), (70, 40), (120, 55), (150, 100)], thickness=NIB_THICKNESS * 0.85)
    return _trace(ring, stem, entry, ctx=ctx)


def glyph_c(ctx: DesignContext | None = None) -> ComposedGlyph:
    # Open bowl: most of an oval, gap on the right.
    cx, cy, rx, ry = 165, 210, 100, 200
    # From NE around to SE, leaving aperture.
    segs = (
        _C((cx + rx * 0.35, cy + ry * 0.85), (cx - K * rx, cy + ry), (cx - rx, cy + K * ry), (cx - rx, cy)),
        _C((cx - rx, cy), (cx - rx, cy - K * ry), (cx - K * rx, cy - ry), (cx, cy - ry)),
        _C((cx, cy - ry), (cx + K * rx, cy - ry), (cx + rx, cy - K * ry), (cx + rx * 0.45, cy - ry * 0.75)),
    )
    entry = _poly("entry", [(30, 95), (80, 45), (130, 70)], thickness=NIB_THICKNESS * 0.85)
    exit_ = _poly("exit", [(cx + rx * 0.45, cy - ry * 0.75), (cx + rx * 0.9, cy - 40), (cx + rx + 40, 70)])
    return _trace(_stroke("bowl", segs), entry, exit_, ctx=ctx)


def glyph_e(ctx: DesignContext | None = None) -> ComposedGlyph:
    # Script e: oval with eye cut by a bar through the bowl.
    ring = _stroke("ring", _ellipse(160, 210, 95, 195), closed=True)
    bar = _poly("bar", [(70, 230), (250, 245)], thickness=NIB_THICKNESS * 0.75)
    entry = _poly("entry", [(25, 100), (80, 45), (130, 80)], thickness=NIB_THICKNESS * 0.85)
    exit_ = _poly("exit", [(240, 80), (290, 30), (350, 55), (390, 95)])
    return _trace(ring, bar, entry, exit_, ctx=ctx)


def glyph_d(ctx: DesignContext | None = None) -> ComposedGlyph:
    ring = _stroke("ring", _ellipse(155, 210, 92, 195), closed=True)
    # Ascender loop on the right (florid letter-writing d).
    asc = _poly(
        "asc",
        [
            (230, 360),
            (250, 500),
            (240, 680),
            (180, 760),
            (120, 720),
            (150, 620),
            (250, 200),
            (270, 40),
            (320, 15),
            (390, 60),
        ],
    )
    entry = _poly("entry", [(25, 95), (80, 40), (130, 70)], thickness=NIB_THICKNESS * 0.85)
    return _trace(ring, asc, entry, ctx=ctx)


def glyph_h(ctx: DesignContext | None = None) -> ComposedGlyph:
    # Ascender stem + arch to right exit (cursive h).
    stem = _poly(
        "stem",
        [(60, 20), (80, 200), (90, 500), (70, 740), (120, 780), (160, 720), (140, 500), (120, 40)],
    )
    arch = _poly(
        "arch",
        [(120, 280), (180, 400), (280, 410), (340, 300), (350, 40), (400, 15), (460, 60)],
    )
    entry = _poly("entry", [(10, 90), (40, 35), (70, 50)], thickness=NIB_THICKNESS * 0.85)
    return _trace(stem, arch, entry, ctx=ctx)


def glyph_i(ctx: DesignContext | None = None) -> ComposedGlyph:
    stem = _poly("stem", [(50, 30), (70, 200), (90, 400), (100, 30), (150, 15), (210, 55)])
    entry = _poly("entry", [(15, 85), (40, 40), (60, 55)], thickness=NIB_THICKNESS * 0.8)
    # Tittle as a short stroke (not a sans ball).
    dot = _poly("dot", [(95, 520), (110, 560), (95, 580), (80, 560), (95, 520)], thickness=NIB_THICKNESS * 0.9)
    return _trace(stem, entry, dot, ctx=ctx)


def glyph_j(ctx: DesignContext | None = None) -> ComposedGlyph:
    # Descender with loop; tittle above.
    body = _poly(
        "body",
        [
            (40, 90),
            (70, 40),
            (100, 200),
            (110, 400),
            (100, 20),
            (90, -120),
            (40, -260),
            (-20, -280),
            (-40, -200),
            (20, -80),
            (90, 20),
            (140, 15),
            (200, 55),
        ],
    )
    dot = _poly("dot", [(100, 520), (115, 560), (100, 580), (85, 560), (100, 520)], thickness=NIB_THICKNESS * 0.9)
    return _trace(body, dot, ctx=ctx)


def glyph_r(ctx: DesignContext | None = None) -> ComposedGlyph:
    stem = _poly("stem", [(40, 25), (55, 200), (70, 400), (80, 40), (120, 20)])
    shoulder = _poly(
        "shoulder",
        [(70, 320), (120, 400), (200, 390), (240, 320), (250, 200)],
        thickness=NIB_THICKNESS * 0.95,
    )
    entry = _poly("entry", [(10, 85), (30, 40), (50, 55)], thickness=NIB_THICKNESS * 0.8)
    exit_ = _poly("exit", [(250, 200), (280, 80), (320, 30), (380, 60)])
    return _trace(stem, shoulder, entry, exit_, ctx=ctx)


def glyph_s(ctx: DesignContext | None = None) -> ComposedGlyph:
    # Flowing script s (spine).
    spine = _poly(
        "spine",
        [
            (40, 120),
            (100, 50),
            (200, 40),
            (280, 100),
            (260, 200),
            (160, 250),
            (100, 300),
            (120, 380),
            (220, 410),
            (300, 360),
            (320, 280),
        ],
    )
    entry = _poly("entry", [(15, 160), (30, 100), (50, 120)], thickness=NIB_THICKNESS * 0.8)
    exit_ = _poly("exit", [(320, 280), (350, 180), (380, 60), (430, 40)])
    return _trace(spine, entry, exit_, ctx=ctx)


def glyph_u(ctx: DesignContext | None = None) -> ComposedGlyph:
    left = _poly("left", [(40, 400), (55, 200), (70, 40), (120, 15), (170, 50), (190, 120)])
    right = _poly(
        "right",
        [(170, 120), (190, 280), (210, 400), (230, 40), (280, 12), (350, 55)],
    )
    entry = _poly("entry", [(15, 95), (35, 45), (55, 80)], thickness=NIB_THICKNESS * 0.8)
    return _trace(left, right, entry, ctx=ctx)


def glyph_v(ctx: DesignContext | None = None) -> ComposedGlyph:
    body = _poly(
        "body",
        [
            (30, 400),
            (80, 200),
            (130, 30),
            (160, 20),
            (200, 80),
            (260, 280),
            (310, 400),
            (340, 360),
        ],
    )
    entry = _poly("entry", [(15, 100), (30, 50), (45, 90)], thickness=NIB_THICKNESS * 0.8)
    exit_ = _poly("exit", [(340, 360), (360, 200), (390, 50), (440, 40)])
    return _trace(body, entry, exit_, ctx=ctx)


def glyph_w(ctx: DesignContext | None = None) -> ComposedGlyph:
    body = _poly(
        "body",
        [
            (30, 400),
            (70, 180),
            (110, 30),
            (140, 25),
            (180, 120),
            (220, 30),
            (260, 25),
            (300, 140),
            (350, 400),
            (390, 340),
        ],
    )
    entry = _poly("entry", [(15, 100), (30, 50), (45, 90)], thickness=NIB_THICKNESS * 0.8)
    exit_ = _poly("exit", [(390, 340), (420, 180), (450, 50), (500, 40)])
    return _trace(body, entry, exit_, ctx=ctx)


def glyph_y(ctx: DesignContext | None = None) -> ComposedGlyph:
    # v-like upper + descender loop.
    body = _poly(
        "body",
        [
            (30, 400),
            (80, 200),
            (130, 40),
            (170, 20),
            (220, 100),
            (280, 320),
            (300, 400),
            (290, 200),
            (270, 20),
            (240, -140),
            (180, -280),
            (100, -290),
            (60, -200),
            (120, -80),
            (220, 40),
            (300, 20),
            (360, 55),
        ],
    )
    entry = _poly("entry", [(15, 100), (30, 50), (45, 90)], thickness=NIB_THICKNESS * 0.8)
    return _trace(body, entry, ctx=ctx)


def glyph_z(ctx: DesignContext | None = None) -> ComposedGlyph:
    # Florid z with top entry and bottom exit.
    body = _poly(
        "body",
        [
            (20, 140),
            (80, 50),
            (220, 40),
            (320, 90),
            (300, 180),
            (120, 280),
            (80, 340),
            (140, 400),
            (280, 410),
            (340, 360),
            (300, 200),
            (200, 80),
            (160, 20),
            (120, -40),
            (180, -20),
            (280, 30),
            (360, 60),
        ],
    )
    return _trace(body, ctx=ctx)


def glyph_D(ctx: DesignContext | None = None) -> ComposedGlyph:
    """Flourished capital D for ``Discover``."""
    # Continuous stem + bowl + top swash as one calligraphy path where possible.
    stem = _poly(
        "stem",
        [
            (50, 20),
            (70, 220),
            (85, 480),
            (95, 680),
            (80, 720),
            (50, 700),
            (70, 520),
            (85, 280),
            (95, 60),
            (130, 25),
        ],
    )
    bowl = _poly(
        "bowl",
        [
            (95, 680),
            (220, 740),
            (380, 680),
            (460, 480),
            (450, 260),
            (340, 60),
            (180, 30),
            (110, 50),
        ],
        thickness=NIB_THICKNESS * 1.08,
    )
    swash = _poly(
        "swash",
        [(-60, 580), (-20, 720), (80, 800), (220, 790), (340, 720), (360, 660)],
        thickness=NIB_THICKNESS * 0.72,
    )
    entry = _poly("entry", [(-20, 50), (20, 5), (55, 30)], thickness=NIB_THICKNESS * 0.7)
    return _trace(stem, bowl, swash, entry, ctx=ctx)


BUILDERS: dict[str, Callable[[DesignContext | None], ComposedGlyph]] = {
    "a": glyph_a,
    "c": glyph_c,
    "d": glyph_d,
    "e": glyph_e,
    "h": glyph_h,
    "i": glyph_i,
    "j": glyph_j,
    "o": glyph_o,
    "r": glyph_r,
    "s": glyph_s,
    "u": glyph_u,
    "v": glyph_v,
    "w": glyph_w,
    "y": glyph_y,
    "z": glyph_z,
    "D": glyph_D,
}


def build_charset(ctx: DesignContext | None = None) -> dict[str, ComposedGlyph]:
    c = ctx or script_context()
    return {ch: fn(c) for ch, fn in BUILDERS.items()}


BRIEF_SENTENCE = "zayju Discover everywhere"
CHARSET = "".join(BUILDERS)  # letters only; space from Font

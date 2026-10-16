"""Florid English letter-writing script — hand-built stroke topologies.

Brief: ``zayju Discover everywhere``.

Pipeline (library-first):
1. Dense slanted centerlines → polyline→cubic fit → contrast-nib expand
2. ``trace_letter`` heal + strip + blend (typekernel base APIs)

Slant is baked into coordinates — not ``oblique_font``.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from typing import Final

from typekernel.geo.stroke import CubicBezier
from typekernel.parts import (
    ComposedGlyph,
    DesignContext,
    Skeleton,
    Stroke,
    trace_letter,
)

SLANT_DEG: Final = 28.0
SHEAR: Final = math.tan(math.radians(SLANT_DEG))
K: Final = 0.5523

NIB_THICKNESS: Final = 36.0
NIB_CONTRAST: Final = 0.48
NIB_ANGLE: Final = 38.0

X_HEIGHT: Final = 420.0
CAP_HEIGHT: Final = 700.0
ASCENDER: Final = 780.0
DESCENDER: Final = -300.0

ENTRY_Y: Final = 58.0
EXIT_Y: Final = 58.0
RAIL_LIFT: Final = 100.0
MIN_CONTOUR_AREA: Final = 350.0


def script_context() -> DesignContext:
    return DesignContext.display().tuned(
        stem=NIB_THICKNESS,
        x_height=X_HEIGHT,
        cap_height=CAP_HEIGHT,
        ascender=ASCENDER,
        descender=DESCENDER,
        overshoot=14.0,
        sidebearing_ratio=0.045,
        contrast=NIB_CONTRAST,
        roundness=0.2,
        aperture=0.55,
    )


def _S(x: float, y: float) -> tuple[float, float]:
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
    return (
        _C((cx + rx, cy), (cx + rx, cy + K * ry), (cx + K * rx, cy + ry), (cx, cy + ry)),
        _C((cx, cy + ry), (cx - K * rx, cy + ry), (cx - rx, cy + K * ry), (cx - rx, cy)),
        _C((cx - rx, cy), (cx - rx, cy - K * ry), (cx - K * rx, cy - ry), (cx, cy - ry)),
        _C((cx, cy - ry), (cx + K * rx, cy - ry), (cx + rx, cy - K * ry), (cx + rx, cy)),
    )


def _chaikin(pts: Sequence[tuple[float, float]], rounds: int = 4) -> list[tuple[float, float]]:
    cur = [tuple(p) for p in pts]
    for _ in range(rounds):
        nxt: list[tuple[float, float]] = [cur[0]]
        for i in range(len(cur) - 1):
            a, b = cur[i], cur[i + 1]
            nxt.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            nxt.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        nxt.append(cur[-1])
        cur = nxt
    return cur


def _poly(
    name: str,
    pts: list[tuple[float, float]],
    *,
    thickness: float | None = None,
    smooth: int = 4,
) -> Stroke:
    dense = _chaikin(pts, rounds=smooth)
    return Stroke.from_points(
        name,
        [_S(*p) for p in dense],
        thickness=thickness if thickness is not None else NIB_THICKNESS,
        contrast=NIB_CONTRAST,
        angle_deg=NIB_ANGLE,
        join="round",
        cap="round",
    )


def _ring(
    name: str,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    *,
    thickness: float | None = None,
) -> Stroke:
    return Stroke.from_beziers(
        name,
        _ellipse(cx, cy, rx, ry),
        closed=True,
        thickness=thickness if thickness is not None else NIB_THICKNESS,
        contrast=NIB_CONTRAST,
        angle_deg=NIB_ANGLE,
        join="round",
        cap="round",
    )


def _entry_rail(x0: float, x1: float, *, y: float = ENTRY_Y) -> list[tuple[float, float]]:
    mid = (x0 + x1) / 2.0
    return [(x0, y + 20.0), (mid, y - 6.0), (x1, RAIL_LIFT)]


def _exit_rail(x0: float, x1: float, *, y: float = EXIT_Y) -> list[tuple[float, float]]:
    mid = (x0 + x1) / 2.0
    return [(x0, RAIL_LIFT * 0.5), (mid, y - 6.0), (x1, y + 28.0)]


def _trace(*strokes: Stroke, ctx: DesignContext | None = None) -> ComposedGlyph:
    # Library polyline→cubic expand + heal/strip/blend keep outlines smooth.
    return trace_letter(
        Skeleton.of(*strokes),
        ctx or script_context(),
        union=True,
        blend=True,
        ease=False,
        join="round",
        cap="round",
        heal=True,
        min_contour_area=MIN_CONTOUR_AREA,
    )


# ---------------------------------------------------------------------------
# Glyphs
# ---------------------------------------------------------------------------


def glyph_o(ctx: DesignContext | None = None) -> ComposedGlyph:
    return _trace(_ring("ring", 175, 210, 100, 200), ctx=ctx)


def glyph_a(ctx: DesignContext | None = None) -> ComposedGlyph:
    ring = _ring("ring", 155, 210, 92, 195)
    stem = _poly("stem", [(208, 310), (240, 170), (255, 45), (310, 15), (390, 55), (430, 95)])
    entry = _poly("entry", _entry_rail(18, 135) + [(168, 175)], thickness=NIB_THICKNESS * 0.9)
    return _trace(ring, stem, entry, ctx=ctx)


def glyph_c(ctx: DesignContext | None = None) -> ComposedGlyph:
    # Open C as a long arc (not closed ring).
    body = _poly(
        "body",
        [
            (250, 360),
            (180, 400),
            (90, 360),
            (50, 250),
            (55, 140),
            (120, 50),
            (210, 35),
            (280, 80),
            (300, 140),
        ],
    )
    entry = _poly("entry", _entry_rail(25, 100) + [(150, 150)], thickness=NIB_THICKNESS * 0.88)
    exit_ = _poly("exit", [(300, 140), *_exit_rail(320, 420)])
    return _trace(body, entry, exit_, ctx=ctx)


def glyph_e(ctx: DesignContext | None = None) -> ComposedGlyph:
    """Script e: left entry → small eye loop → right exit (single stroke)."""
    body = _poly(
        "body",
        [
            (25, ENTRY_Y + 15),
            (80, ENTRY_Y - 5),
            (140, 110),
            (175, 210),
            (150, 320),
            (95, 365),
            (55, 300),
            (85, 210),
            (155, 175),
            (240, 120),
            (310, 55),
            (390, EXIT_Y + 25),
        ],
    )
    return _trace(body, ctx=ctx)


def glyph_d(ctx: DesignContext | None = None) -> ComposedGlyph:
    ring = _ring("ring", 155, 210, 92, 195)
    asc = _poly(
        "asc",
        [
            (210, 300),
            (245, 470),
            (235, 670),
            (170, 755),
            (115, 700),
            (155, 540),
            (245, 170),
            (265, 40),
            (335, 12),
            (415, 70),
        ],
    )
    entry = _poly("entry", _entry_rail(20, 130) + [(160, 170)], thickness=NIB_THICKNESS * 0.88)
    return _trace(ring, asc, entry, ctx=ctx)


def glyph_h(ctx: DesignContext | None = None) -> ComposedGlyph:
    stem = _poly(
        "stem",
        [
            (55, ENTRY_Y),
            (75, 200),
            (90, 480),
            (75, 710),
            (115, 765),
            (155, 700),
            (135, 380),
            (120, 70),
        ],
    )
    arch = _poly(
        "arch",
        [
            (120, 255),
            (175, 385),
            (275, 395),
            (345, 275),
            (360, 55),
            (410, 15),
            (480, EXIT_Y + 28),
        ],
    )
    return _trace(stem, arch, ctx=ctx)


def glyph_i(ctx: DesignContext | None = None) -> ComposedGlyph:
    stem = _poly(
        "stem",
        [
            (45, ENTRY_Y + 12),
            (65, 40),
            (85, 230),
            (100, 400),
            (110, 45),
            (160, 12),
            (230, EXIT_Y + 25),
        ],
    )
    dot = _ring("dot", 100, 555, 16, 20, thickness=NIB_THICKNESS * 0.65)
    return _trace(stem, dot, ctx=ctx)


def glyph_j(ctx: DesignContext | None = None) -> ComposedGlyph:
    body = _poly(
        "body",
        [
            (55, ENTRY_Y + 15),
            (85, 40),
            (110, 240),
            (120, 400),
            (105, 40),
            (90, -140),
            (45, -270),
            (0, -285),
            (-25, -200),
            (40, -50),
            (110, 20),
            (170, 12),
            (240, EXIT_Y + 25),
        ],
    )
    dot = _ring("dot", 110, 555, 16, 20, thickness=NIB_THICKNESS * 0.65)
    return _trace(body, dot, ctx=ctx)


def glyph_r(ctx: DesignContext | None = None) -> ComposedGlyph:
    stem = _poly(
        "stem",
        [(50, ENTRY_Y), (65, 200), (80, 400), (95, 45), (140, 15)],
    )
    shoulder = _poly(
        "shoulder",
        [(80, 290), (140, 390), (220, 375), (255, 270), (265, 150)],
    )
    exit_ = _poly("exit", [(265, 150), *_exit_rail(285, 410)])
    return _trace(stem, shoulder, exit_, ctx=ctx)


def glyph_s(ctx: DesignContext | None = None) -> ComposedGlyph:
    """Script s: top curve, spine, bottom curve — recognizable serpentine."""
    body = _poly(
        "body",
        [
            (40, 150),
            (100, 55),
            (200, 40),
            (285, 85),
            (275, 165),
            (190, 235),
            (110, 295),
            (105, 365),
            (175, 420),
            (275, 400),
            (325, 310),
            (340, 180),
            (365, 70),
            (440, EXIT_Y + 20),
        ],
    )
    entry = _poly("entry", _entry_rail(15, 55, y=ENTRY_Y + 35), thickness=NIB_THICKNESS * 0.88)
    return _trace(body, entry, ctx=ctx)


def glyph_u(ctx: DesignContext | None = None) -> ComposedGlyph:
    body = _poly(
        "body",
        [
            (35, ENTRY_Y + 8),
            (55, 40),
            (70, 230),
            (80, 400),
            (95, 55),
            (145, 12),
            (195, 55),
            (215, 280),
            (235, 400),
            (255, 45),
            (310, 12),
            (390, EXIT_Y + 28),
        ],
    )
    return _trace(body, ctx=ctx)


def glyph_v(ctx: DesignContext | None = None) -> ComposedGlyph:
    body = _poly(
        "body",
        [
            (40, 400),
            (100, 170),
            (155, 25),
            (185, 22),
            (235, 130),
            (295, 340),
            (330, 400),
            (360, 260),
            (395, 70),
            (460, EXIT_Y + 25),
        ],
    )
    entry = _poly("entry", _entry_rail(18, 50, y=ENTRY_Y + 28) + [(55, 310)], thickness=NIB_THICKNESS * 0.88)
    return _trace(body, entry, ctx=ctx)


def glyph_w(ctx: DesignContext | None = None) -> ComposedGlyph:
    body = _poly(
        "body",
        [
            (35, 400),
            (75, 150),
            (115, 25),
            (150, 25),
            (185, 140),
            (220, 25),
            (260, 25),
            (300, 150),
            (345, 400),
            (385, 260),
            (430, 65),
            (500, EXIT_Y + 25),
        ],
    )
    entry = _poly("entry", _entry_rail(15, 45, y=ENTRY_Y + 28) + [(50, 310)], thickness=NIB_THICKNESS * 0.88)
    return _trace(body, entry, ctx=ctx)


def glyph_y(ctx: DesignContext | None = None) -> ComposedGlyph:
    body = _poly(
        "body",
        [
            (35, 400),
            (95, 170),
            (150, 28),
            (185, 22),
            (240, 140),
            (295, 360),
            (310, 400),
            (295, 170),
            (265, 20),
            (225, -160),
            (155, -290),
            (75, -275),
            (50, -175),
            (120, -35),
            (230, 30),
            (310, 15),
            (395, EXIT_Y + 25),
        ],
    )
    entry = _poly("entry", _entry_rail(15, 45, y=ENTRY_Y + 28) + [(50, 310)], thickness=NIB_THICKNESS * 0.88)
    return _trace(body, entry, ctx=ctx)


def glyph_z(ctx: DesignContext | None = None) -> ComposedGlyph:
    """Script z: top bar → diagonal → bottom with light descender exit."""
    body = _poly(
        "body",
        [
            (30, 155),
            (90, 50),
            (230, 40),
            (305, 75),
            (270, 155),
            (155, 275),
            (105, 355),
            (160, 425),
            (275, 420),
            (335, 345),
            (295, 195),
            (195, 65),
            (155, -5),
            (215, -30),
            (330, 25),
            (415, EXIT_Y + 22),
        ],
    )
    return _trace(body, ctx=ctx)


def glyph_D(ctx: DesignContext | None = None) -> ComposedGlyph:
    """Capital D: one continuous stem→swash→bowl path (recognizable, welded)."""
    body = _poly(
        "body",
        [
            (35, 55),
            (70, 40),
            (95, 200),
            (110, 450),
            (115, 690),
            (70, 750),
            (-35, 640),
            (30, 790),
            (170, 820),
            (320, 770),
            (445, 620),
            (495, 420),
            (465, 195),
            (330, 55),
            (170, 35),
            (100, 55),
        ],
        thickness=NIB_THICKNESS * 1.12,
    )
    return _trace(body, ctx=ctx)


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
CHARSET = "".join(BUILDERS)

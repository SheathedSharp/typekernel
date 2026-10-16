"""Florid English letter-writing script — hand-built stroke topologies.

Late specimen phrase (not the design driver): ``zayju Discover everywhere``.

Designer order (required):
1. Control glyphs first (``a`` body + ``o`` bowl), then one letter at a time
2. Each new glyph is style-checked against control / previous via
   ``typekernel.qa.style_consistency``
3. Only after the gated sequence unlocks the charset do we compose the brief PNG

Pipeline (library-first per glyph):
- Dense slanted centerlines → polyline→cubic fit → contrast-nib expand
- ``trace_letter`` heal + strip + blend

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
    entry = _poly("entry", _entry_rail(12, 48), thickness=NIB_THICKNESS * 0.88)
    stem = _poly(
        "stem",
        [(50, ENTRY_Y), (62, 200), (75, 380), (90, 50), (130, 20)],
        thickness=NIB_THICKNESS * 0.95,
    )
    shoulder = _poly(
        "shoulder",
        [(75, 280), (135, 380), (215, 365), (250, 260), (260, 140)],
    )
    exit_ = _poly("exit", [(260, 140), *_exit_rail(280, 410)])
    return _trace(entry, stem, shoulder, exit_, ctx=ctx)


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
    entry = _poly("entry", _entry_rail(15, 55, y=ENTRY_Y), thickness=NIB_THICKNESS * 0.88)
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
    entry = _poly("entry", _entry_rail(18, 50, y=ENTRY_Y) + [(50, 280)], thickness=NIB_THICKNESS * 0.88)
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
    entry = _poly("entry", _entry_rail(12, 45, y=ENTRY_Y), thickness=NIB_THICKNESS * 0.88)
    return _trace(entry, body, ctx=ctx)


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


# Control first (body rails + bowl), then remaining letters one at a time.
# Ascenders/descenders/caps come after body letters share stem/rail language.
DESIGN_ORDER: Final[tuple[str, ...]] = (
    "a",  # control: entry/exit rails + bowl
    "o",  # bowl control
    "e",
    "c",
    "u",
    "r",
    "v",
    "w",
    "s",
    "i",
    "y",
    "z",
    "d",
    "h",
    "j",
    "D",
)
CONTROL_GLYPH: Final = "a"

# Late specimen only — never the design method.
BRIEF_SENTENCE: Final = "zayju Discover everywhere"
CHARSET: Final = "".join(DESIGN_ORDER)


def build_charset(ctx: DesignContext | None = None) -> dict[str, ComposedGlyph]:
    """Build every letter (no style gate). Prefer :func:`build_charset_sequential`."""
    c = ctx or script_context()
    return {ch: BUILDERS[ch](c) for ch in DESIGN_ORDER}


_CLOSED_BOWLS: Final = frozenset({"o", "O"})
_ASCENDERS: Final = frozenset({"d", "h", "D", "l", "b", "k", "f", "t"})
_DESCENDERS: Final = frozenset({"j", "y", "g", "p", "q"})


def _script_skip_checks(ref: str, cand: str) -> tuple[str, ...]:
    """Omit metrics that are meaningless across topology roles."""
    skip: list[str] = []
    if ref in _CLOSED_BOWLS or cand in _CLOSED_BOWLS:
        skip.extend(["entry_rail_y", "exit_rail_y", "exit_slant_deg"])
    if cand in _ASCENDERS or ref in _ASCENDERS:
        skip.extend(["ink_ymax", "bowl_center_y", "exit_rail_y", "exit_slant_deg"])
    if cand in _DESCENDERS or ref in _DESCENDERS:
        skip.extend(["ink_ymin", "bowl_center_y", "entry_rail_y"])
    # Dotted / short letters: vertical exits are not writing rails.
    if cand in {"i", "j"} or ref in {"i", "j"}:
        skip.extend(["exit_rail_y", "exit_slant_deg", "ink_ymax", "bowl_center_y"])
    return tuple(dict.fromkeys(skip))


def script_sequence_tolerances():
    """Florid-script budgets: shared stem/rails; contrast slack for open vs closed."""
    from typekernel.qa.style_consistency import StyleConsistencyTolerances

    return StyleConsistencyTolerances(
        stem_median=18.0,
        contrast_ratio=1.45,
        entry_rail_y=52.0,
        exit_rail_y=52.0,
        exit_slant_deg=110.0,  # florid diagonals (z) vs round exits
        bowl_center_y=60.0,
        ink_ymin=60.0,
        ink_ymax=120.0,
    )


def build_charset_sequential(
    ctx: DesignContext | None = None,
    *,
    tolerances: object | None = None,
    compare_to_previous: bool = True,
) -> tuple[dict[str, ComposedGlyph], object]:
    """Design-order build: one glyph at a time, then style-check vs control/previous.

    Returns ``(drawn, sequence_report)``. Agents must not treat a failing report
    as success — fix the candidate glyph before unlocking the next letter.
    """
    from typekernel.qa.style_consistency import check_design_sequence

    c = ctx or script_context()
    drawn: dict[str, ComposedGlyph] = {}
    for ch in DESIGN_ORDER:
        # One at a time — do not batch-construct without reading the prior letter.
        drawn[ch] = BUILDERS[ch](c)
    tol = tolerances if tolerances is not None else script_sequence_tolerances()
    report = check_design_sequence(
        drawn,
        DESIGN_ORDER,
        control=CONTROL_GLYPH,
        tolerances=tol,  # type: ignore[arg-type]
        compare_to_previous=compare_to_previous,
        skip_checks_for_pair=_script_skip_checks,
    )
    return drawn, report

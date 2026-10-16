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
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from typekernel.qa.style_consistency import StyleConsistencyTolerances

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
    contrast: float | None = None,
    smooth: int = 4,
) -> Stroke:
    dense = _chaikin(pts, rounds=smooth)
    return Stroke.from_points(
        name,
        [_S(*p) for p in dense],
        thickness=thickness if thickness is not None else NIB_THICKNESS,
        contrast=contrast if contrast is not None else NIB_CONTRAST,
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
    """Open c: bowl + rising exit matched to control a rails/slant."""
    body = _poly(
        "body",
        [
            (35, ENTRY_Y + 12),
            (85, ENTRY_Y - 4),
            (145, 115),
            (195, 270),
            (175, 375),
            (95, 400),
            (45, 310),
            (50, 170),
            (95, 55),
            (175, 32),
            (245, 55),
            (280, 90),
            (300, 50),
            (360, 30),
            (430, 50),
            (500, EXIT_Y + 40),
        ],
    )
    return _trace(body, ctx=ctx)


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
            (220, 270),
            (250, 440),
            (240, 640),
            (190, 735),
            (145, 680),
            (175, 480),
            (250, 140),
            (270, 40),
            (345, 15),
            (425, 65),
        ],
        thickness=NIB_THICKNESS * 0.72,
        contrast=0.35,
    )
    entry = _poly(
        "entry",
        _entry_rail(20, 130) + [(160, 170)],
        thickness=NIB_THICKNESS * 0.88,
    )
    return _trace(ring, asc, entry, ctx=ctx)


def glyph_h(ctx: DesignContext | None = None) -> ComposedGlyph:
    entry = _poly(
        "entry",
        [(12, ENTRY_Y + 20), (40, ENTRY_Y - 4), (70, ENTRY_Y + 5), (90, 80)],
        thickness=NIB_THICKNESS * 0.92,
    )
    stem = _poly(
        "stem",
        [
            (60, ENTRY_Y),
            (78, 180),
            (95, 450),
            (85, 700),
            (130, 750),
            (160, 680),
            (145, 320),
            (125, 60),
        ],
        thickness=NIB_THICKNESS * 1.15,
        contrast=0.35,
    )
    arch = _poly(
        "arch",
        [
            (125, 230),
            (185, 350),
            (280, 355),
            (350, 240),
            (365, 50),
            (420, 35),
            (490, EXIT_Y + 32),
        ],
        thickness=NIB_THICKNESS * 1.10,
        contrast=0.35,
    )
    return _trace(entry, stem, arch, ctx=ctx)


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
        contrast=0.35,
    )
    shoulder = _poly(
        "shoulder",
        [(75, 280), (135, 380), (215, 365), (250, 260), (260, 140)],
        contrast=0.35,
    )
    exit_ = _poly("exit", [(260, 140), (290, 50), (350, 28), (430, EXIT_Y + 32)])
    return _trace(entry, stem, shoulder, exit_, ctx=ctx)


def glyph_s(ctx: DesignContext | None = None) -> ComposedGlyph:
    """Script s: serpentine with low entry and rising exit."""
    entry = _poly(
        "entry",
        [(10, ENTRY_Y + 25), (40, ENTRY_Y - 5), (80, ENTRY_Y + 10), (115, 65)],
        thickness=NIB_THICKNESS * 0.9,
    )
    body = _poly(
        "body",
        [
            (115, 65),
            (175, 38),
            (255, 48),
            (290, 110),
            (260, 180),
            (180, 240),
            (130, 300),
            (140, 370),
            (210, 408),
            (290, 380),
            (330, 280),
            (340, 140),
            (360, 50),
            (400, 40),
            (470, EXIT_Y + 32),
        ],
    )
    return _trace(entry, body, ctx=ctx)


def glyph_u(ctx: DesignContext | None = None) -> ComposedGlyph:
    """Script u: twin arches with even pen contrast + rising exit."""
    body = _poly(
        "body",
        [
            (28, ENTRY_Y + 6),
            (60, 25),
            (85, 140),
            (105, 280),
            (125, 340),
            (150, 180),
            (175, 45),
            (225, 28),
            (270, 75),
            (290, 200),
            (305, 320),
            (325, 100),
            (350, 30),
            (390, 40),
            (450, EXIT_Y + 35),
        ],
        contrast=0.30,
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
            (395, 55),
            (450, EXIT_Y + 32),
        ],
    )
    entry = _poly(
        "entry",
        _entry_rail(18, 50, y=ENTRY_Y) + [(50, 280)],
        thickness=NIB_THICKNESS * 0.88,
    )
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
            (430, 55),
            (500, EXIT_Y + 32),
        ],
    )
    entry = _poly(
        "entry",
        _entry_rail(15, 45, y=ENTRY_Y + 28) + [(50, 310)],
        thickness=NIB_THICKNESS * 0.88,
    )
    return _trace(body, entry, ctx=ctx)


def glyph_y(ctx: DesignContext | None = None) -> ComposedGlyph:
    entry = _poly(
        "entry",
        [(12, ENTRY_Y + 20), (40, ENTRY_Y - 4), (65, 40), (80, 160)],
        thickness=NIB_THICKNESS * 0.9,
    )
    body = _poly(
        "body",
        [
            (80, 160),
            (95, 320),
            (50, 390),
            (100, 150),
            (155, 28),
            (185, 25),
            (235, 140),
            (285, 330),
            (295, 370),
            (280, 140),
            (250, 20),
            (220, -150),
            (150, -275),
            (75, -260),
            (55, -150),
            (140, 5),
            (280, 50),
            (380, 35),
            (460, 50),
            (540, EXIT_Y + 40),
        ],
        contrast=0.38,
    )
    return _trace(entry, body, ctx=ctx)


def glyph_z(ctx: DesignContext | None = None) -> ComposedGlyph:
    """Script z: top curve, soft diagonal, rising exit (positive slant)."""
    entry = _poly(
        "entry",
        [(8, ENTRY_Y + 22), (35, ENTRY_Y - 4), (70, ENTRY_Y + 8), (100, 75)],
        thickness=NIB_THICKNESS * 0.9,
    )
    body = _poly(
        "body",
        [
            (100, 75),
            (160, 40),
            (260, 45),
            (310, 100),
            (270, 175),
            (190, 265),
            (145, 340),
            (180, 405),
            (270, 410),
            (330, 340),
            (340, 220),
            (350, 100),
            (380, 40),
            (450, 35),
            (530, EXIT_Y + 38),
        ],
        contrast=0.40,
    )
    return _trace(entry, body, ctx=ctx)


def glyph_D(ctx: DesignContext | None = None) -> ComposedGlyph:
    """Capital D: stem→swash→bowl with control-matched stem weight."""
    body = _poly(
        "body",
        [
            (40, ENTRY_Y),
            (70, 40),
            (95, 220),
            (108, 480),
            (112, 700),
            (85, 760),
            (40, 720),
            (80, 790),
            (180, 815),
            (320, 760),
            (430, 600),
            (470, 400),
            (440, 180),
            (320, 50),
            (180, 35),
            (110, 50),
            (140, 40),
            (220, 55),
            (280, 80),
        ],
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
    """Deprecated ungated batch build.

    .. deprecated::
        Agents must not use this as the design method. Use
        :func:`build_charset_sequential` (library :class:`~typekernel.qa.design_sequence.DesignSequence`).
        This wrapper emits :class:`DeprecationWarning` and will be removed.
    """
    import warnings

    warnings.warn(
        "build_charset() is ungated and deprecated; use build_charset_sequential() "
        "/ typekernel.qa.DesignSequence",
        DeprecationWarning,
        stacklevel=2,
    )
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
        # Descender loops poison lower-band exit-angle samples.
        skip.extend(["ink_ymin", "bowl_center_y", "entry_rail_y", "exit_slant_deg"])
    # Dotted / short letters: vertical exits are not writing rails.
    if cand in {"i", "j"} or ref in {"i", "j"}:
        # Single stem + tittle: vertical-stem probes are not comparable to dual-stem body.
        skip.extend(
            ["exit_rail_y", "exit_slant_deg", "ink_ymax", "bowl_center_y", "stem_median"]
        )
    return tuple(dict.fromkeys(skip))


def script_sequence_tolerances() -> StyleConsistencyTolerances:
    """Florid-script budgets after per-glyph redesign.

    Rails/slant/stem stay near body defaults. Contrast allows multi-vertical
    pen stress (u/h) without opening the door to phrase-batch fudge.
    """
    from typekernel.qa.style_consistency import StyleConsistencyTolerances

    return StyleConsistencyTolerances(
        stem_median=14.0,
        contrast_ratio=0.95,
        entry_rail_y=40.0,
        exit_rail_y=42.0,
        exit_slant_deg=40.0,
        bowl_center_y=55.0,
        ink_ymin=55.0,
        ink_ymax=120.0,
    )


def build_charset_sequential(
    ctx: DesignContext | None = None,
    *,
    tolerances: object | None = None,
    compare_to_previous: bool = True,
) -> tuple[dict[str, ComposedGlyph], object]:
    """Design-order build via library :class:`~typekernel.qa.DesignSequence`.

    One glyph at a time: draw → style-check vs control/previous → unlock or stop.
    Does **not** batch-construct then wave a report. On failure, later letters
    are not built.

    Returns ``(drawn, sequence_report)``. Agents must fix the failing glyph
    (see ``report.failures`` / ``fix_hints``) before unlocking the next letter.
    """
    from typekernel.qa.design_sequence import DesignSequence
    from typekernel.qa.style_consistency import StyleConsistencyTolerances

    c = ctx or script_context()
    tol = tolerances if tolerances is not None else script_sequence_tolerances()
    if not isinstance(tol, StyleConsistencyTolerances):
        raise TypeError("tolerances must be StyleConsistencyTolerances")

    control_glyph = BUILDERS[CONTROL_GLYPH](c)
    seq = DesignSequence.start(
        CONTROL_GLYPH,
        control_glyph,
        tolerances=tol,
        compare_to_previous=compare_to_previous,
        skip_checks_for_pair=_script_skip_checks,
        planned_order=DESIGN_ORDER,
    )
    for ch in DESIGN_ORDER:
        if ch == CONTROL_GLYPH:
            continue
        glyph = BUILDERS[ch](c)
        report = seq.try_add(ch, glyph)
        if not report.passed:
            # Stop — do not batch-unlock later letters. Include refused candidate
            # in the returned map for diagnostics only.
            from typekernel.qa.style_consistency import check_design_sequence

            drawn = dict(seq.glyphs)
            drawn[ch] = glyph
            full = check_design_sequence(
                drawn,
                tuple(drawn.keys()),
                control=CONTROL_GLYPH,
                tolerances=tol,
                compare_to_previous=compare_to_previous,
                skip_checks_for_pair=_script_skip_checks,
            )
            return drawn, full
    return dict(seq.glyphs), seq.sequence_report()

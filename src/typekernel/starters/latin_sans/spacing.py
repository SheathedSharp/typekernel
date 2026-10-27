"""Metrics keys + sidebearings + kern pairs (ARCHITECTURE.md §3.2 / M4.33).

Project-side only — no letter builders. ``apply_spacing`` packs each glyph so
ink starts at the resolved LSB and advance = LSB + ink + RSB, then writes
pair kerning onto the Font. Wired from ``tk build`` via ``cli.load``.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from typekernel.draw.geomutil import map_segment
from typekernel.font.font import Font
from typekernel.font.glyph import Glyph
from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline, bounds
from typekernel.geo.point import Point
from typekernel.system import System

__all__ = [
    "KERN_PAIRS",
    "METRICS_KEYS",
    "apply_spacing",
    "resolve_sidebearings",
]


# Tracy / Glyphs-style keys. Values:
#   float                         → absolute design units
#   ("stem", key, factor)         → system.stem[key] * factor
#   ("ref", glyph, "lsb"|"rsb")   → copy that side from another glyph's resolved bearing
# Keys are resolved in dependency order (refs after bases).
METRICS_KEYS: dict[str, dict[str, Any]] = {
    # controls
    "n": {"lsb": ("stem", "lc", 0.9), "rsb": ("stem", "lc", 0.9)},
    "o": {"lsb": ("stem", "lc", 0.55), "rsb": ("stem", "lc", 0.55)},
    "H": {"lsb": ("stem", "uc", 0.85), "rsb": ("stem", "uc", 0.85)},
    "O": {"lsb": ("stem", "uc", 0.5), "rsb": ("stem", "uc", 0.5)},
    # n-group
    "h": {"lsb": ("ref", "n", "lsb"), "rsb": ("ref", "n", "rsb")},
    "m": {"lsb": ("ref", "n", "lsb"), "rsb": ("ref", "n", "rsb")},
    "u": {"lsb": ("ref", "n", "lsb"), "rsb": ("ref", "n", "rsb")},
    "r": {"lsb": ("ref", "n", "lsb"), "rsb": ("stem", "lc", 0.45)},
    "i": {"lsb": ("stem", "lc", 1.0), "rsb": ("stem", "lc", 1.0)},
    "l": {"lsb": ("ref", "i", "lsb"), "rsb": ("ref", "i", "rsb")},
    "j": {"lsb": ("stem", "lc", 0.4), "rsb": ("ref", "i", "rsb")},
    "f": {"lsb": ("stem", "lc", 0.35), "rsb": ("stem", "lc", 0.25)},
    "t": {"lsb": ("stem", "lc", 0.35), "rsb": ("stem", "lc", 0.45)},
    # o-group
    "b": {"lsb": ("ref", "n", "lsb"), "rsb": ("ref", "o", "rsb")},
    "d": {"lsb": ("ref", "o", "lsb"), "rsb": ("ref", "n", "rsb")},
    "p": {"lsb": ("ref", "n", "lsb"), "rsb": ("ref", "o", "rsb")},
    "q": {"lsb": ("ref", "o", "lsb"), "rsb": ("ref", "n", "rsb")},
    "c": {"lsb": ("ref", "o", "lsb"), "rsb": ("stem", "lc", 0.35)},
    "e": {"lsb": ("ref", "o", "lsb"), "rsb": ("ref", "o", "rsb")},
    "a": {"lsb": ("stem", "lc", 0.45), "rsb": ("ref", "n", "rsb")},
    "g": {"lsb": ("ref", "o", "lsb"), "rsb": ("ref", "o", "rsb")},
    "s": {"lsb": ("stem", "lc", 0.5), "rsb": ("stem", "lc", 0.5)},
    # diagonals
    "v": {"lsb": ("stem", "lc", 0.2), "rsb": ("stem", "lc", 0.2)},
    "w": {"lsb": ("stem", "lc", 0.15), "rsb": ("stem", "lc", 0.15)},
    "x": {"lsb": ("stem", "lc", 0.25), "rsb": ("stem", "lc", 0.25)},
    "y": {"lsb": ("stem", "lc", 0.2), "rsb": ("stem", "lc", 0.2)},
    "z": {"lsb": ("stem", "lc", 0.4), "rsb": ("stem", "lc", 0.4)},
    "k": {"lsb": ("ref", "n", "lsb"), "rsb": ("stem", "lc", 0.25)},
    # caps H-group
    "I": {"lsb": ("stem", "uc", 1.0), "rsb": ("stem", "uc", 1.0)},
    "L": {"lsb": ("ref", "H", "lsb"), "rsb": ("stem", "uc", 0.35)},
    "E": {"lsb": ("ref", "H", "lsb"), "rsb": ("stem", "uc", 0.4)},
    "F": {"lsb": ("ref", "H", "lsb"), "rsb": ("stem", "uc", 0.35)},
    "T": {"lsb": ("stem", "uc", 0.25), "rsb": ("stem", "uc", 0.25)},
    "N": {"lsb": ("ref", "H", "lsb"), "rsb": ("ref", "H", "rsb")},
    "M": {"lsb": ("ref", "H", "lsb"), "rsb": ("ref", "H", "rsb")},
    "U": {"lsb": ("ref", "H", "lsb"), "rsb": ("ref", "H", "rsb")},
    "B": {"lsb": ("ref", "H", "lsb"), "rsb": ("ref", "O", "rsb")},
    "P": {"lsb": ("ref", "H", "lsb"), "rsb": ("stem", "uc", 0.4)},
    "R": {"lsb": ("ref", "H", "lsb"), "rsb": ("stem", "uc", 0.3)},
    "D": {"lsb": ("ref", "H", "lsb"), "rsb": ("ref", "O", "rsb")},
    "J": {"lsb": ("stem", "uc", 0.35), "rsb": ("ref", "H", "rsb")},
    # caps O-group / diagonals
    "C": {"lsb": ("ref", "O", "lsb"), "rsb": ("stem", "uc", 0.3)},
    "G": {"lsb": ("ref", "O", "lsb"), "rsb": ("ref", "O", "rsb")},
    "Q": {"lsb": ("ref", "O", "lsb"), "rsb": ("ref", "O", "rsb")},
    "S": {"lsb": ("stem", "uc", 0.45), "rsb": ("stem", "uc", 0.45)},
    "A": {"lsb": ("stem", "uc", 0.15), "rsb": ("stem", "uc", 0.15)},
    "V": {"lsb": ("stem", "uc", 0.15), "rsb": ("stem", "uc", 0.15)},
    "W": {"lsb": ("stem", "uc", 0.1), "rsb": ("stem", "uc", 0.1)},
    "X": {"lsb": ("stem", "uc", 0.2), "rsb": ("stem", "uc", 0.2)},
    "Y": {"lsb": ("stem", "uc", 0.15), "rsb": ("stem", "uc", 0.15)},
    "Z": {"lsb": ("stem", "uc", 0.35), "rsb": ("stem", "uc", 0.35)},
    "K": {"lsb": ("ref", "H", "lsb"), "rsb": ("stem", "uc", 0.2)},
    # figures — tabular-ish
    "zero": {"lsb": ("stem", "lc", 0.5), "rsb": ("stem", "lc", 0.5)},
    "one": {"lsb": ("stem", "lc", 0.5), "rsb": ("stem", "lc", 0.5)},
    "two": {"lsb": ("stem", "lc", 0.5), "rsb": ("stem", "lc", 0.5)},
    "three": {"lsb": ("stem", "lc", 0.5), "rsb": ("stem", "lc", 0.5)},
    "four": {"lsb": ("stem", "lc", 0.5), "rsb": ("stem", "lc", 0.5)},
    "five": {"lsb": ("stem", "lc", 0.5), "rsb": ("stem", "lc", 0.5)},
    "six": {"lsb": ("stem", "lc", 0.5), "rsb": ("stem", "lc", 0.5)},
    "seven": {"lsb": ("stem", "lc", 0.5), "rsb": ("stem", "lc", 0.5)},
    "eight": {"lsb": ("stem", "lc", 0.5), "rsb": ("stem", "lc", 0.5)},
    "nine": {"lsb": ("stem", "lc", 0.5), "rsb": ("stem", "lc", 0.5)},
    # punctuation
    "period": {"lsb": ("stem", "lc", 0.55), "rsb": ("stem", "lc", 0.55)},
    "comma": {"lsb": ("stem", "lc", 0.55), "rsb": ("stem", "lc", 0.55)},
    "colon": {"lsb": ("stem", "lc", 0.6), "rsb": ("stem", "lc", 0.6)},
    "semicolon": {"lsb": ("stem", "lc", 0.6), "rsb": ("stem", "lc", 0.6)},
    "exclam": {"lsb": ("stem", "lc", 0.7), "rsb": ("stem", "lc", 0.7)},
    "question": {"lsb": ("stem", "lc", 0.4), "rsb": ("stem", "lc", 0.4)},
    "quotesingle": {"lsb": ("stem", "lc", 0.7), "rsb": ("stem", "lc", 0.7)},
    "quotedbl": {"lsb": ("stem", "lc", 0.5), "rsb": ("stem", "lc", 0.5)},
    "hyphen": {"lsb": ("stem", "lc", 0.45), "rsb": ("stem", "lc", 0.45)},
    "endash": {"lsb": ("stem", "lc", 0.35), "rsb": ("stem", "lc", 0.35)},
    "emdash": {"lsb": ("stem", "lc", 0.25), "rsb": ("stem", "lc", 0.25)},
    "parenleft": {"lsb": ("stem", "lc", 0.55), "rsb": ("stem", "lc", 0.35)},
    "parenright": {"lsb": ("stem", "lc", 0.35), "rsb": ("stem", "lc", 0.55)},
    "bracketleft": {"lsb": ("stem", "lc", 0.55), "rsb": ("stem", "lc", 0.35)},
    "bracketright": {"lsb": ("stem", "lc", 0.35), "rsb": ("stem", "lc", 0.55)},
    "slash": {"lsb": ("stem", "lc", 0.3), "rsb": ("stem", "lc", 0.3)},
    "backslash": {"lsb": ("stem", "lc", 0.3), "rsb": ("stem", "lc", 0.3)},
}


# Proof kern strings from ARCH §3.3: AV Ta To Yo LT P. F,
KERN_PAIRS: tuple[tuple[str, str, float], ...] = (
    ("A", "V", -48.0),
    ("A", "W", -36.0),
    ("A", "Y", -40.0),
    ("V", "A", -48.0),
    ("W", "A", -36.0),
    ("Y", "A", -40.0),
    ("T", "a", -36.0),
    ("T", "o", -40.0),
    ("T", "e", -36.0),
    ("T", "y", -28.0),
    ("F", "a", -28.0),
    ("F", "o", -24.0),
    ("F", "comma", -48.0),
    ("F", "period", -48.0),
    ("P", "a", -24.0),
    ("P", "o", -20.0),
    ("P", "period", -56.0),
    ("P", "comma", -56.0),
    ("L", "T", -40.0),
    ("L", "V", -36.0),
    ("L", "Y", -40.0),
    ("Y", "o", -32.0),
    ("Y", "a", -28.0),
    ("V", "o", -28.0),
    ("V", "a", -24.0),
    ("r", "a", -8.0),
    ("r", "o", -6.0),
    ("f", "a", -6.0),
    ("f", "o", -4.0),
    ("f", "period", -20.0),
    ("f", "comma", -20.0),
    ("quotedbl", "A", -12.0),
    ("quotesingle", "A", -12.0),
)


def _eval_side(expr: Any, system: System, resolved: dict[str, tuple[float, float]]) -> float:
    if isinstance(expr, (int, float)):
        return float(expr)
    if not isinstance(expr, tuple) or not expr:
        raise TypeError(f"bad metrics key expression: {expr!r}")
    kind = expr[0]
    if kind == "stem":
        _, stem_key, factor = expr
        return float(system.stem[stem_key]) * float(factor)
    if kind == "ref":
        _, ref_name, side = expr
        if ref_name not in resolved:
            raise KeyError(f"metrics key ref {ref_name!r} not resolved yet")
        lsb, rsb = resolved[ref_name]
        return lsb if side == "lsb" else rsb
    if kind == "token":
        _, token_key, factor = expr
        return float(system.tokens[token_key]) * float(factor)
    raise ValueError(f"unknown metrics key kind: {kind!r}")


def resolve_sidebearings(system: System) -> dict[str, tuple[float, float]]:
    """Resolve METRICS_KEYS to ``{name: (lsb, rsb)}`` in dependency order."""
    resolved: dict[str, tuple[float, float]] = {}
    pending = dict(METRICS_KEYS)
    # Multi-pass so refs can point at earlier keys.
    for _ in range(len(pending) + 2):
        if not pending:
            break
        progressed = False
        for name, sides in list(pending.items()):
            try:
                lsb = _eval_side(sides["lsb"], system, resolved)
                rsb = _eval_side(sides["rsb"], system, resolved)
            except KeyError:
                continue
            resolved[name] = (lsb, rsb)
            del pending[name]
            progressed = True
        if not progressed:
            break
    if pending:
        raise ValueError(f"unresolved metrics keys (cycle or missing ref): {sorted(pending)}")
    return resolved


def _translate_outline(outline: Outline, dx: float, dy: float = 0.0) -> Outline:
    def move(p: Point) -> Point:
        return Point(p.x + dx, p.y + dy)

    return Outline(
        tuple(
            Contour(tuple(map_segment(s, move) for s in c.segments), closed=c.closed)
            for c in outline.contours
        )
    )


def _pack_glyph(glyph: Glyph, lsb: float, rsb: float) -> Glyph:
    """Shift ink so xmin == lsb; advance = lsb + ink_width + rsb."""
    if not glyph.outline.contours or not any(c.segments for c in glyph.outline.contours):
        # empty (space): keep advance or use lsb+rsb as width hint
        return replace(glyph, advance=max(glyph.advance, lsb + rsb))
    min_x, _miny, max_x, _maxy = bounds(glyph.outline)
    ink = float(max_x - min_x)
    dx = lsb - float(min_x)
    shifted = _translate_outline(glyph.outline, dx)
    return replace(glyph, outline=shifted, advance=lsb + ink + rsb)


def apply_spacing(font: Font, system: System) -> dict[str, tuple[float, float]]:
    """Pack sidebearings from metrics keys and write KERN_PAIRS onto ``font``.

    Glyphs without a metrics key keep their existing advance (token / bbox).
    Returns the resolved ``{name: (lsb, rsb)}`` table for diagnostics.
    """
    resolved = resolve_sidebearings(system)
    for name, (lsb, rsb) in resolved.items():
        if name not in font:
            continue
        font.add_glyph(_pack_glyph(font[name], lsb, rsb), replace=True)

    # Default space width from n rhythm when present.
    if "space" in font and "n" in resolved:
        n_lsb, n_rsb = resolved["n"]
        space_adv = float(system.stem["lc"]) * 2.5 + n_lsb * 0.5
        g = font["space"]
        font.add_glyph(replace(g, advance=space_adv), replace=True)

    for left, right, value in KERN_PAIRS:
        left_n = font.resolve(left)
        right_n = font.resolve(right)
        if left_n is None or right_n is None:
            continue
        font.kerning[(left_n, right_n)] = float(value)

    return resolved

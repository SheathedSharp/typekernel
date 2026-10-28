"""Metrics keys + sidebearings + kern for latin-chancery (project-side).

Italic packing uses multi-y silhouette samples (``tokens["italic_pack_ys"]``)
instead of a single mid-x-height scan — better for slanted stems / flourishes.
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

METRICS_KEYS: dict[str, dict[str, Any]] = {
    # controls / bases
    "n": {"lsb": ("stem", "lc", 0.85), "rsb": ("stem", "lc", 0.85)},
    "o": {"lsb": ("stem", "lc", 0.5), "rsb": ("stem", "lc", 0.5)},
    "H": {"lsb": ("stem", "uc", 0.8), "rsb": ("stem", "uc", 0.8)},
    "O": {"lsb": ("stem", "uc", 0.45), "rsb": ("stem", "uc", 0.45)},
    # n-group
    "h": {"lsb": ("ref", "n", "lsb"), "rsb": ("ref", "n", "rsb")},
    "m": {"lsb": ("ref", "n", "lsb"), "rsb": ("ref", "n", "rsb")},
    "u": {"lsb": ("ref", "n", "lsb"), "rsb": ("ref", "n", "rsb")},
    "r": {"lsb": ("ref", "n", "lsb"), "rsb": ("stem", "lc", 0.4)},
    "i": {"lsb": ("stem", "lc", 1.0), "rsb": ("stem", "lc", 1.0)},
    "l": {"lsb": ("ref", "i", "lsb"), "rsb": ("ref", "i", "rsb")},
    "j": {"lsb": ("stem", "lc", 0.35), "rsb": ("ref", "i", "rsb")},
    "f": {"lsb": ("stem", "lc", 0.3), "rsb": ("stem", "lc", 0.25)},
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
    # caps
    "I": {"lsb": ("stem", "uc", 1.0), "rsb": ("stem", "uc", 1.0)},
    "L": {"lsb": ("ref", "H", "lsb"), "rsb": ("stem", "uc", 0.28)},
    "E": {"lsb": ("ref", "H", "lsb"), "rsb": ("stem", "uc", 0.4)},
    "F": {"lsb": ("ref", "H", "lsb"), "rsb": ("stem", "uc", 0.35)},
    "T": {"lsb": ("stem", "uc", 0.22), "rsb": ("stem", "uc", 0.22)},
    "N": {"lsb": ("ref", "H", "lsb"), "rsb": ("ref", "H", "rsb")},
    "M": {"lsb": ("ref", "H", "lsb"), "rsb": ("ref", "H", "rsb")},
    "U": {"lsb": ("ref", "H", "lsb"), "rsb": ("ref", "H", "rsb")},
    "B": {"lsb": ("ref", "H", "lsb"), "rsb": ("ref", "O", "rsb")},
    "P": {"lsb": ("ref", "H", "lsb"), "rsb": ("stem", "uc", 0.4)},
    "R": {"lsb": ("ref", "H", "lsb"), "rsb": ("stem", "uc", 0.25)},
    "D": {"lsb": ("ref", "H", "lsb"), "rsb": ("ref", "O", "rsb")},
    "J": {"lsb": ("stem", "uc", 0.35), "rsb": ("ref", "H", "rsb")},
    "C": {"lsb": ("ref", "O", "lsb"), "rsb": ("stem", "uc", 0.3)},
    "G": {"lsb": ("ref", "O", "lsb"), "rsb": ("stem", "uc", 0.35)},
    "Q": {"lsb": ("ref", "O", "lsb"), "rsb": ("ref", "O", "rsb")},
    "S": {"lsb": ("stem", "uc", 0.45), "rsb": ("stem", "uc", 0.45)},
    "A": {"lsb": ("stem", "uc", 0.2), "rsb": ("stem", "uc", 0.2)},
    "V": {"lsb": ("stem", "uc", 0.18), "rsb": ("stem", "uc", 0.18)},
    "W": {"lsb": ("stem", "uc", 0.15), "rsb": ("stem", "uc", 0.15)},
    "X": {"lsb": ("stem", "uc", 0.22), "rsb": ("stem", "uc", 0.22)},
    "Y": {"lsb": ("stem", "uc", 0.2), "rsb": ("stem", "uc", 0.2)},
    "Z": {"lsb": ("stem", "uc", 0.35), "rsb": ("stem", "uc", 0.35)},
    "K": {"lsb": ("ref", "H", "lsb"), "rsb": ("stem", "uc", 0.22)},
    # figures
    "zero": {"lsb": ("stem", "lc", 0.45), "rsb": ("stem", "lc", 0.45)},
    "one": {"lsb": ("stem", "lc", 0.7), "rsb": ("stem", "lc", 0.7)},
    "two": {"lsb": ("stem", "lc", 0.4), "rsb": ("stem", "lc", 0.4)},
    "three": {"lsb": ("stem", "lc", 0.4), "rsb": ("stem", "lc", 0.4)},
    "four": {"lsb": ("stem", "lc", 0.35), "rsb": ("stem", "lc", 0.4)},
    "five": {"lsb": ("stem", "lc", 0.4), "rsb": ("stem", "lc", 0.4)},
    "six": {"lsb": ("stem", "lc", 0.45), "rsb": ("stem", "lc", 0.45)},
    "seven": {"lsb": ("stem", "lc", 0.35), "rsb": ("stem", "lc", 0.4)},
    "eight": {"lsb": ("stem", "lc", 0.45), "rsb": ("stem", "lc", 0.45)},
    "nine": {"lsb": ("stem", "lc", 0.45), "rsb": ("stem", "lc", 0.45)},
    # punct
    "period": {"lsb": ("stem", "lc", 0.55), "rsb": ("stem", "lc", 0.55)},
    "comma": {"lsb": ("ref", "period", "lsb"), "rsb": ("ref", "period", "rsb")},
    "colon": {"lsb": ("ref", "period", "lsb"), "rsb": ("ref", "period", "rsb")},
    "semicolon": {"lsb": ("ref", "period", "lsb"), "rsb": ("ref", "period", "rsb")},
    "exclam": {"lsb": ("stem", "lc", 0.7), "rsb": ("stem", "lc", 0.7)},
    "question": {"lsb": ("stem", "lc", 0.45), "rsb": ("stem", "lc", 0.45)},
    "hyphen": {"lsb": ("stem", "lc", 0.4), "rsb": ("stem", "lc", 0.4)},
    "quotesingle": {"lsb": ("stem", "lc", 0.7), "rsb": ("stem", "lc", 0.7)},
    "quotedbl": {"lsb": ("stem", "lc", 0.55), "rsb": ("stem", "lc", 0.55)},
    "parenleft": {"lsb": ("stem", "lc", 0.45), "rsb": ("stem", "lc", 0.25)},
    "parenright": {"lsb": ("stem", "lc", 0.25), "rsb": ("stem", "lc", 0.45)},
    "slash": {"lsb": ("stem", "lc", 0.25), "rsb": ("stem", "lc", 0.25)},
}

KERN_PAIRS: list[tuple[str, str, float]] = [
    # lc
    ("o", "n", -10.0),
    ("n", "o", -8.0),
    ("a", "v", -18.0),
    ("a", "w", -16.0),
    ("a", "y", -18.0),
    ("r", "o", -6.0),
    ("r", "a", -4.0),
    ("v", "a", -16.0),
    ("v", "o", -12.0),
    ("v", "e", -12.0),
    ("w", "a", -14.0),
    ("w", "o", -10.0),
    ("y", "a", -16.0),
    ("y", "o", -12.0),
    ("y", "e", -12.0),
    ("f", "o", -8.0),
    ("f", "a", -6.0),
    ("t", "o", -4.0),
    ("c", "o", -4.0),
    ("e", "v", -10.0),
    ("e", "w", -8.0),
    ("e", "y", -10.0),
    ("o", "v", -12.0),
    ("o", "w", -10.0),
    ("o", "x", -8.0),
    ("o", "y", -12.0),
    ("k", "o", -10.0),
    ("k", "a", -8.0),
    ("x", "o", -8.0),
    ("x", "a", -6.0),
    # uc
    ("A", "V", -28.0),
    ("A", "W", -24.0),
    ("A", "Y", -30.0),
    ("A", "T", -20.0),
    ("T", "A", -22.0),
    ("T", "o", -18.0),
    ("T", "a", -16.0),
    ("T", "e", -16.0),
    ("V", "A", -28.0),
    ("V", "o", -20.0),
    ("V", "a", -18.0),
    ("W", "A", -24.0),
    ("W", "o", -16.0),
    ("Y", "A", -30.0),
    ("Y", "o", -22.0),
    ("Y", "a", -20.0),
    ("F", "A", -18.0),
    ("F", "a", -14.0),
    ("P", "A", -22.0),
    ("P", "a", -16.0),
    ("L", "T", -16.0),
    ("L", "V", -18.0),
    ("L", "Y", -20.0),
    ("H", "O", -10.0),
    ("R", "o", -8.0),
    ("D", "A", -8.0),
    # punct
    ("period", "quotedbl", -4.0),
    ("comma", "quotedbl", -4.0),
]


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
    resolved: dict[str, tuple[float, float]] = {}
    pending = dict(METRICS_KEYS)
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
        raise ValueError(f"unresolved metrics keys: {sorted(pending)}")
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


def _italic_silhouette_span(
    outline: Outline, system: System
) -> tuple[float, float] | None:
    """Leftmost/rightmost silhouette across several y bands in the x-height.

    Beats single mid-x-height packing for slanted stems, bowls, and flourishes.
    """
    from typekernel.optics.space import silhouette_edge

    xh = float(system.zones.x)
    fracs = system.tokens.get("italic_pack_ys", (0.28, 0.5, 0.72))
    lefts: list[float] = []
    rights: list[float] = []
    for frac in fracs:
        y = xh * float(frac)
        left = silhouette_edge([outline], y, "left")
        right = silhouette_edge([outline], y, "right")
        if left is not None:
            lefts.append(float(left))
        if right is not None:
            rights.append(float(right))
    if not lefts or not rights:
        return None
    return min(lefts), max(rights)


def _pack_glyph(glyph: Glyph, lsb: float, rsb: float, system: System | None = None) -> Glyph:
    if not glyph.outline.contours or not any(c.segments for c in glyph.outline.contours):
        return replace(glyph, advance=max(glyph.advance, lsb + rsb))
    if system is not None and system.is_italic:
        span = _italic_silhouette_span(glyph.outline, system)
        if span is not None:
            left, right = span
            ink = float(right - left)
            dx = lsb - float(left)
            shifted = _translate_outline(glyph.outline, dx)
            return replace(glyph, outline=shifted, advance=lsb + ink + rsb)
    min_x, _miny, max_x, _maxy = bounds(glyph.outline)
    ink = float(max_x - min_x)
    dx = lsb - float(min_x)
    shifted = _translate_outline(glyph.outline, dx)
    return replace(glyph, outline=shifted, advance=lsb + ink + rsb)


def apply_spacing(font: Font, system: System) -> dict[str, tuple[float, float]]:
    resolved = resolve_sidebearings(system)
    for name, (lsb, rsb) in resolved.items():
        if name not in font:
            continue
        font.add_glyph(_pack_glyph(font[name], lsb, rsb, system), replace=True)

    if "space" in font:
        tokens = system.tokens
        if "space_advance" in tokens:
            space_adv = float(tokens["space_advance"])
        elif "n" in resolved:
            n_lsb, _n_rsb = resolved["n"]
            stem_mul = float(tokens.get("space_stem_mul", 2.5))
            lsb_mul = float(tokens.get("space_lsb_mul", 0.5))
            space_adv = float(system.stem["lc"]) * stem_mul + n_lsb * lsb_mul
        else:
            space_adv = None
        if space_adv is not None:
            g = font["space"]
            font.add_glyph(replace(g, advance=space_adv), replace=True)

    for left, right, value in KERN_PAIRS:
        left_n = font.resolve(left)
        right_n = font.resolve(right)
        if left_n is None or right_n is None:
            continue
        font.kerning[(left_n, right_n)] = float(value)

    return resolved

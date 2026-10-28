"""Metrics keys + sidebearings + kern for latin-chancery (project-side)."""

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
    "n": {"lsb": ("stem", "lc", 0.85), "rsb": ("stem", "lc", 0.85)},
    "o": {"lsb": ("stem", "lc", 0.5), "rsb": ("stem", "lc", 0.5)},
    "e": {"lsb": ("stem", "lc", 0.5), "rsb": ("stem", "lc", 0.45)},
    "h": {"lsb": ("ref", "n", "lsb"), "rsb": ("ref", "n", "rsb")},
    "H": {"lsb": ("stem", "uc", 0.8), "rsb": ("stem", "uc", 0.8)},
    "O": {"lsb": ("stem", "uc", 0.45), "rsb": ("stem", "uc", 0.45)},
}

KERN_PAIRS: list[tuple[str, str, float]] = [
    ("o", "n", -8.0),
    ("n", "o", -6.0),
    ("H", "O", -10.0),
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


def _pack_glyph(glyph: Glyph, lsb: float, rsb: float, system: System | None = None) -> Glyph:
    if not glyph.outline.contours or not any(c.segments for c in glyph.outline.contours):
        return replace(glyph, advance=max(glyph.advance, lsb + rsb))
    if system is not None and system.is_italic:
        from typekernel.optics.space import silhouette_edge

        y = float(system.zones.x) * 0.5
        left = silhouette_edge([glyph.outline], y, "left")
        right = silhouette_edge([glyph.outline], y, "right")
        if left is not None and right is not None:
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

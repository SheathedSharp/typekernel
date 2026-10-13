"""Masters — designed fonts placed on design axes, checked before interpolation.

A variable family is a set of fully designed :class:`~typekernel.font.Font`
masters (for example Light and Bold drawn from two control sheets), each at a
location such as ``{"wght": 300}``. :func:`check_masters` catches everything
that would make them fail to interpolate before any binary is built.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from typekernel.axes.interpolatable import check_interpolatable
from typekernel.font.font import Font

__all__ = ["AXIS_NAMES", "Master", "axis_ranges", "check_masters"]

AXIS_NAMES: dict[str, str] = {
    "wght": "Weight",
    "wdth": "Width",
    "opsz": "Optical size",
    "slnt": "Slant",
    "ital": "Italic",
}
"""Registered axis tags → designspace axis names; other tags use the tag."""


@dataclass(frozen=True, slots=True)
class Master:
    """One designed font at an axis location (user coordinates)."""

    location: Mapping[str, float]
    font: Font
    name: str = field(default="")

    @property
    def style_name(self) -> str:
        return self.name or self.font.info.style_name


def axis_ranges(masters: Sequence[Master]) -> dict[str, tuple[float, float, float]]:
    """``{tag: (minimum, default, maximum)}``; the first master is the default."""
    default = masters[0].location
    return {
        tag: (
            min(m.location[tag] for m in masters),
            default[tag],
            max(m.location[tag] for m in masters),
        )
        for tag in default
    }


def check_masters(masters: Sequence[Master]) -> list[str]:
    """Return problems that would stop ``masters`` from interpolating (empty = OK)."""
    if len(masters) < 2:
        return ["need at least two masters"]
    problems: list[str] = []
    ref = masters[0]
    tags = set(ref.location)
    if not tags:
        problems.append("masters have no axis locations")

    seen: dict[tuple[tuple[str, float], ...], str] = {}
    for m in masters:
        label = m.style_name
        if set(m.location) != tags:
            problems.append(f"master {label!r} axes {sorted(m.location)} != {sorted(tags)}")
            continue
        key = tuple(sorted(m.location.items()))
        if key in seen:
            problems.append(f"masters {seen[key]!r} and {label!r} share location {dict(key)}")
        seen[key] = label
        if m.font.info.family_name != ref.font.info.family_name:
            problems.append(
                f"master {label!r} family {m.font.info.family_name!r} "
                f"!= {ref.font.info.family_name!r}"
            )
        problems.extend(f"master {label!r}: {p}" for p in m.font.validate())
    if problems:
        return problems

    for tag, (lo, _, hi) in axis_ranges(masters).items():
        if lo == hi:
            problems.append(f"axis {tag!r} does not vary across masters")

    order = ref.font.glyph_order
    for m in masters[1:]:
        if m.font.glyph_order != order:
            missing = sorted(set(order) ^ set(m.font.glyph_order))
            detail = f"differs by {missing}" if missing else "has a different order"
            problems.append(f"master {m.style_name!r} glyph set {detail}")
        if m.font.groups != ref.font.groups:
            problems.append(f"master {m.style_name!r} kerning groups differ")
    if problems:
        return problems

    for name in order:
        glyphs = [m.font[name] for m in masters]
        for issue in check_interpolatable([g.outline for g in glyphs]):
            problems.append(f"glyph {name!r}: {issue}")
        first = glyphs[0]
        for m, g in zip(masters[1:], glyphs[1:], strict=True):
            if [c.base for c in g.components] != [c.base for c in first.components]:
                problems.append(f"glyph {name!r} components differ in {m.style_name!r}")
            if sorted(a.name for a in g.anchors) != sorted(a.name for a in first.anchors):
                problems.append(f"glyph {name!r} anchors differ in {m.style_name!r}")
            if g.unicodes != first.unicodes:
                problems.append(f"glyph {name!r} unicodes differ in {m.style_name!r}")
    return problems

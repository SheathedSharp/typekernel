"""Typed per-glyph design knobs (between global floats and hand-built outlines)."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from typing import Any

from typekernel.parts.caps import G_from_O, R_from_H, Y_from_H
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext
from typekernel.parts.control import (
    a_from_o,
    e_from_o,
    f_from_n,
    j_from_n,
    s_from_o,
    t_from_n,
)

__all__ = [
    "WEAK_GLYPH_SPECS",
    "ASpec",
    "ESpec",
    "FSpec",
    "GSpec",
    "JSpec",
    "RSpec",
    "SSpec",
    "TSpec",
    "YSpec",
    "build_from_spec",
    "merge_spec",
    "spec_fields",
]


@dataclass(frozen=True, slots=True)
class FSpec:
    """``f``: shoulder arm length (``r`` terminal placement)."""

    arm: float = 0.75


@dataclass(frozen=True, slots=True)
class TSpec:
    """``t``: hook arm and how high the stem rises below the ascender."""

    arm: float = 0.6
    rise: float = 0.3


@dataclass(frozen=True, slots=True)
class JSpec:
    """``j``: descender hook arm."""

    arm: float = 0.75


@dataclass(frozen=True, slots=True)
class ASpec:
    """``a``: bowl-to-stem join tightness."""

    join: float = 0.85


@dataclass(frozen=True, slots=True)
class ESpec:
    """``e``: crossbar height and optional aperture override."""

    bar_raise: float = 0.25
    aperture: float | None = None


@dataclass(frozen=True, slots=True)
class SSpec:
    """``s``: spine position and bowl widths."""

    width: float = 0.82
    top_scale: float = 0.90
    spine: float = 0.50
    aperture: float | None = None


@dataclass(frozen=True, slots=True)
class GSpec:
    """``G``: inward crossbar reach past the cap ``O`` centre."""

    bar_reach: float = 0.1


@dataclass(frozen=True, slots=True)
class RSpec:
    """``R``: bowl width and leg splice along the lower curve."""

    width: float = 0.94
    straight: float = 0.45
    bowl: float = 0.47
    leg_at: float = 0.3


@dataclass(frozen=True, slots=True)
class YSpec:
    """``Y``: arm meeting height on the cap stem."""

    width: float = 0.98
    junction: float = 0.42


WEAK_GLYPH_SPECS: dict[str, type[Any]] = {
    "f": FSpec,
    "t": TSpec,
    "j": JSpec,
    "a": ASpec,
    "e": ESpec,
    "s": SSpec,
    "G": GSpec,
    "R": RSpec,
    "Y": YSpec,
}


def spec_fields(ch: str) -> tuple[str, ...]:
    """Public field names for ``tuned_glyph(ch, **…)``."""
    cls = WEAK_GLYPH_SPECS[ch]
    return tuple(f.name for f in fields(cls))


def merge_spec(ch: str, current: object | None, **kwargs: float) -> object:
    cls = WEAK_GLYPH_SPECS[ch]
    allowed = {f.name for f in fields(cls)}
    unknown = set(kwargs) - allowed
    if unknown:
        raise TypeError(f"{ch} spec has no field(s) {sorted(unknown)!r}; use {sorted(allowed)}")
    base = current if isinstance(current, cls) else cls()
    return replace(base, **kwargs)


def build_from_spec(
    ch: str,
    spec: object,
    n_glyph: ComposedGlyph,
    o_glyph: ComposedGlyph,
    ctx: DesignContext,
) -> ComposedGlyph:
    if ch == "f" and isinstance(spec, FSpec):
        return f_from_n(n_glyph, ctx, arm=spec.arm)
    if ch == "t" and isinstance(spec, TSpec):
        return t_from_n(n_glyph, ctx, arm=spec.arm, rise=spec.rise)
    if ch == "j" and isinstance(spec, JSpec):
        return j_from_n(n_glyph, ctx, arm=spec.arm)
    if ch == "a" and isinstance(spec, ASpec):
        return a_from_o(o_glyph, n_glyph, ctx, join=spec.join)
    if ch == "e" and isinstance(spec, ESpec):
        kw: dict[str, float] = {"bar_raise": spec.bar_raise}
        if spec.aperture is not None:
            kw["aperture"] = spec.aperture
        return e_from_o(o_glyph, ctx, **kw)
    if ch == "s" and isinstance(spec, SSpec):
        kw = {"width": spec.width, "top_scale": spec.top_scale, "spine": spec.spine}
        if spec.aperture is not None:
            kw["aperture"] = spec.aperture
        return s_from_o(o_glyph, ctx, **kw)
    if ch == "G" and isinstance(spec, GSpec):
        return G_from_O(o_glyph, n_glyph, ctx, bar_reach=spec.bar_reach)
    if ch == "R" and isinstance(spec, RSpec):
        return R_from_H(
            n_glyph,
            o_glyph,
            ctx,
            width=spec.width,
            straight=spec.straight,
            bowl=spec.bowl,
            leg_at=spec.leg_at,
        )
    if ch == "Y" and isinstance(spec, YSpec):
        return Y_from_H(n_glyph, ctx, width=spec.width, junction=spec.junction)
    raise KeyError(f"no builder for spec {ch!r}")

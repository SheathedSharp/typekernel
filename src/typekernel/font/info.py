"""Font-wide naming and vertical metrics, derived from the design brief.

The same numbers that shape the letters (x-height, cap height, ascender,
descender, overshoot, stem) also define the font's vertical metrics and
PostScript alignment zones. :meth:`FontInfo.from_context` keeps them in one
place so a family never ships metrics that disagree with its drawings.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Any

from typekernel.parts.context import DesignContext

__all__ = ["FontInfo", "alignment_zones"]

Zone = tuple[float, float]


def _merge_zones(zones: list[Zone]) -> list[Zone]:
    merged: list[Zone] = []
    for lo, hi in sorted(zones):
        if merged and lo <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
        else:
            merged.append((lo, hi))
    return merged


def alignment_zones(ctx: DesignContext) -> tuple[tuple[Zone, ...], tuple[Zone, ...]]:
    """Return ``(blue_zones, other_blues)`` from the context's overshoot.

    Blue zones cover baseline (below), x-height, cap height and ascender
    (above). The descender zone goes to ``other_blues`` as PostScript requires.
    """
    o = abs(ctx.overshoot)
    sharp = abs(ctx.sharp_bump())
    blues = _merge_zones(
        [
            (-o, 0.0),
            (ctx.x_height, ctx.x_height + sharp),
            (ctx.cap_height, ctx.cap_height + sharp),
            (ctx.ascender, ctx.ascender + o),
        ]
    )
    others = _merge_zones([(ctx.descender - o, ctx.descender)])
    return tuple(blues), tuple(others)


def _flat(zones: tuple[Zone, ...]) -> list[int]:
    return [round(v) for zone in zones for v in zone]


@dataclass(frozen=True, slots=True)
class FontInfo:
    """Naming, version and vertical metrics for one font (one style).

    ``line_gap`` is the typographic line gap. ``extra`` passes any other UFO
    ``fontinfo`` attribute through verbatim (for example
    ``{"openTypeNameDesigner": "zayju"}``) and wins over derived values.
    """

    family_name: str
    style_name: str = "Regular"
    units_per_em: float = 1000.0
    ascender: float = 750.0
    descender: float = -250.0
    x_height: float = 500.0
    cap_height: float = 700.0
    line_gap: float = 200.0
    weight_class: int = 400
    version_major: int = 1
    version_minor: int = 0
    blue_zones: tuple[Zone, ...] = ()
    other_blues: tuple[Zone, ...] = ()
    stem_snap_v: tuple[float, ...] = ()
    stem_snap_h: tuple[float, ...] = ()
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.family_name:
            raise ValueError("family_name must be non-empty")
        if self.descender > 0:
            raise ValueError(f"descender must be <= 0, got {self.descender}")
        if not 1 <= self.weight_class <= 1000:
            raise ValueError(f"weight_class must be in 1..1000, got {self.weight_class}")

    @classmethod
    def from_context(
        cls,
        ctx: DesignContext,
        family_name: str,
        style_name: str = "Regular",
        *,
        line_height: float = 1.2,
        weight_class: int = 400,
        **overrides: Any,
    ) -> FontInfo:
        """Derive metrics, zones and stem snaps from a :class:`DesignContext`.

        ``line_height`` (in em) sets the line gap so that
        ``ascender - descender + line_gap == line_height * units_per_em``.
        Remaining keyword arguments override fields of the result.
        """
        body = ctx.ascender - ctx.descender
        blues, others = alignment_zones(ctx)
        info = cls(
            family_name=family_name,
            style_name=style_name,
            units_per_em=ctx.units_per_em,
            ascender=ctx.ascender,
            descender=ctx.descender,
            x_height=ctx.x_height,
            cap_height=ctx.cap_height,
            line_gap=max(0.0, line_height * ctx.units_per_em - body),
            weight_class=weight_class,
            blue_zones=blues,
            other_blues=others,
            stem_snap_v=(ctx.stem,),
            stem_snap_h=(ctx.thin,),
        )
        return replace(info, **overrides) if overrides else info

    def to_ufo_attributes(self) -> dict[str, Any]:
        """UFO ``fontinfo`` attributes (integers where the spec requires them)."""
        asc = round(self.ascender)
        desc = round(self.descender)
        gap = round(self.line_gap)
        attrs: dict[str, Any] = {
            "familyName": self.family_name,
            "styleName": self.style_name,
            "unitsPerEm": round(self.units_per_em),
            "versionMajor": self.version_major,
            "versionMinor": self.version_minor,
            "ascender": asc,
            "descender": desc,
            "xHeight": round(self.x_height),
            "capHeight": round(self.cap_height),
            "openTypeOS2WeightClass": self.weight_class,
            "openTypeOS2TypoAscender": asc,
            "openTypeOS2TypoDescender": desc,
            "openTypeOS2TypoLineGap": gap,
            "openTypeHheaAscender": asc,
            "openTypeHheaDescender": desc,
            "openTypeHheaLineGap": gap,
            # USE_TYPO_METRICS: line spacing follows the typo values above.
            "openTypeOS2Selection": [7],
        }
        if self.blue_zones:
            attrs["postscriptBlueValues"] = _flat(self.blue_zones)
        if self.other_blues:
            attrs["postscriptOtherBlues"] = _flat(self.other_blues)
        if self.stem_snap_v:
            attrs["postscriptStemSnapV"] = [round(v) for v in self.stem_snap_v]
        if self.stem_snap_h:
            attrs["postscriptStemSnapH"] = [round(v) for v in self.stem_snap_h]
        attrs.update(self.extra)
        return attrs

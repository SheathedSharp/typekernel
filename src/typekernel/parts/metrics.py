"""Spacing, sidebearings, and minimal kerning for composed glyphs.

Coding agents need more than raw outlines: advance widths, tracking, and a
small kerning-pair table so a word like ``zayju`` can be laid out without
hand-tuned pixel offsets.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from typekernel.geo.layout import layout_x_positions
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext


@dataclass(frozen=True, slots=True)
class KernPair:
    """One pairwise kerning adjustment in design units.

    ``value`` is added to the advance *between* ``left`` and ``right``
    (negative pulls them closer). Glyph names are single characters or
    PostScript-style names — agents should be consistent within one table.
    """

    left: str
    right: str
    value: float


@dataclass(frozen=True, slots=True)
class KernTable:
    """Minimal kerning dictionary keyed by ``(left, right)``."""

    pairs: tuple[KernPair, ...] = ()

    def lookup(self, left: str, right: str) -> float:
        for p in self.pairs:
            if p.left == left and p.right == right:
                return p.value
        return 0.0

    def with_pair(self, left: str, right: str, value: float) -> KernTable:
        """Return a new table with one pair added or replaced."""
        kept = [p for p in self.pairs if not (p.left == left and p.right == right)]
        kept.append(KernPair(left, right, value))
        return KernTable(tuple(kept))

    @classmethod
    def from_optical(
        cls,
        glyphs: list[ComposedGlyph],
        names: list[str],
        *,
        target_gap: float | None = None,
        samples: int = 17,
    ) -> KernTable:
        """Fit pair kerns so optical silhouette gaps match ``target_gap``.

        Sidebearings are left as-is; only kern values are solved. For a full
        re-space (bearings + kern) prefer
        :func:`typekernel.optics.space.space_word_optical`.
        """
        from typekernel.optics.space import fit_kern_pair, pair_gap_optical

        if len(glyphs) != len(names):
            raise ValueError("names length must match glyphs")
        if target_gap is None:
            gaps = [
                pair_gap_optical(glyphs[i], glyphs[i + 1], kern=0.0, samples=samples)
                for i in range(len(glyphs) - 1)
            ]
            gaps.sort()
            target = gaps[len(gaps) // 2] if gaps else 0.0
        else:
            target = target_gap
        pairs = [
            KernPair(
                names[i],
                names[i + 1],
                fit_kern_pair(glyphs[i], glyphs[i + 1], target, samples=samples),
            )
            for i in range(len(glyphs) - 1)
        ]
        return cls(tuple(pairs))


def default_sans_kern() -> KernTable:
    """Starter kerning for geometric lowercase — tuned so ``zayju`` gaps even out.

    Diagonal pairs (``ay``, ``yj``) pull in; the narrow ``j`` pulls toward ``u``
    so air after the hook does not look larger than ``za``.
    """
    return KernTable(
        (
            KernPair("z", "a", -8.0),
            KernPair("a", "y", -11.0),
            KernPair("y", "j", -11.0),
            KernPair("j", "u", -11.0),
            KernPair("a", "v", -16.0),
            KernPair("v", "a", -16.0),
            KernPair("T", "a", -28.0),
            KernPair("L", "T", -20.0),
        )
    )




@dataclass(frozen=True, slots=True)
class KernClass:
    """Named glyph class for class-based kerning.

    ``members`` are glyph names (single letters or PostScript-style names).
    Order does not matter for lookup; the first member is the default
    representative used by :func:`auto_class_kern` unless overridden.
    """

    name: str
    members: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("KernClass name must be non-empty")
        if not self.members:
            raise ValueError(f"KernClass {self.name!r} needs at least one member")
        # freeze uniqueness check
        if len(set(self.members)) != len(self.members):
            raise ValueError(f"KernClass {self.name!r} has duplicate members")

    def contains(self, glyph: str) -> bool:
        return glyph in self.members

    @property
    def representative(self) -> str:
        return self.members[0]


@dataclass(frozen=True, slots=True)
class ClassKernPair:
    """Kern value between two :class:`KernClass` names."""

    left_class: str
    right_class: str
    value: float


@dataclass(frozen=True, slots=True)
class RhythmSpec:
    """Family spacing rhythm — optical gap target for kern fitting.

    Typically derived from control glyphs (``n``/``o``) via
    :func:`rhythm_from_control_glyphs`.
    """

    target_gap: float
    source: str = "explicit"

    def __post_init__(self) -> None:
        if self.target_gap <= 0:
            raise ValueError(f"target_gap must be positive, got {self.target_gap!r}")


@dataclass(frozen=True, slots=True)
class ClassKernTable:
    """Class-to-class kerning table with optional flat expansion.

    Lookup resolves glyph→class membership then returns the class-pair value
    (0 if missing). Overlapping class membership prefers the first matching
    class in ``classes`` order.
    """

    classes: tuple[KernClass, ...] = ()
    pairs: tuple[ClassKernPair, ...] = ()

    def class_of(self, glyph: str) -> str | None:
        for kc in self.classes:
            if kc.contains(glyph):
                return kc.name
        return None

    def lookup_classes(self, left_class: str, right_class: str) -> float:
        for p in self.pairs:
            if p.left_class == left_class and p.right_class == right_class:
                return p.value
        return 0.0

    def lookup(self, left: str, right: str) -> float:
        """Glyph-level lookup via class membership."""
        lc = self.class_of(left)
        rc = self.class_of(right)
        if lc is None or rc is None:
            return 0.0
        return self.lookup_classes(lc, rc)

    def with_pair(self, left_class: str, right_class: str, value: float) -> ClassKernTable:
        kept = [
            p
            for p in self.pairs
            if not (p.left_class == left_class and p.right_class == right_class)
        ]
        kept.append(ClassKernPair(left_class, right_class, value))
        return ClassKernTable(self.classes, tuple(kept))

    def expand(self) -> KernTable:
        """Explode class pairs into a flat :class:`KernTable` of glyph pairs."""
        by_name = {kc.name: kc for kc in self.classes}
        flat: list[KernPair] = []
        for p in self.pairs:
            left = by_name.get(p.left_class)
            right = by_name.get(p.right_class)
            if left is None or right is None:
                continue
            for a in left.members:
                for b in right.members:
                    flat.append(KernPair(a, b, p.value))
        return KernTable(tuple(flat))

    def to_fea(self, *, feature_name: str = "kern") -> str:
        """Return a minimal Adobe FEA class-kern snippet (compile-layer ready)."""
        fea_lines: list[str] = [f"feature {feature_name} {{"]
        for kc in self.classes:
            members = " ".join(kc.members)
            fea_lines.append(f"  @{kc.name} = [{members}];")
        for pair in self.pairs:
            val = round(pair.value)
            fea_lines.append(f"  pos @{pair.left_class} @{pair.right_class} {val};")
        fea_lines.append(f"}} {feature_name};")
        return "\n".join(fea_lines) + "\n"



def rhythm_from_control_glyphs(
    *controls: ComposedGlyph,
    samples: int = 17,
) -> RhythmSpec:
    """Build a :class:`RhythmSpec` from one or more control glyphs.

    Uses the median optical gap of each control glyph paired with itself
    (kern=0). Pass ``n`` and/or ``o`` (or synthetic stand-ins) as the family
    rhythm anchors.
    """
    from typekernel.optics.space import pair_gap_optical

    if not controls:
        raise ValueError("need at least one control glyph")
    gaps = [
        pair_gap_optical(g, g, kern=0.0, samples=samples) for g in controls
    ]
    gaps.sort()
    mid = gaps[len(gaps) // 2]
    if mid <= 0:
        # Fall back to a fraction of x-height from the first glyph's context
        mid = 0.16 * controls[0].context.x_height
    return RhythmSpec(target_gap=mid, source="control_glyphs")


def auto_class_kern(
    glyphs: Mapping[str, ComposedGlyph],
    classes: Sequence[KernClass],
    *,
    target: RhythmSpec | float | None = None,
    samples: int = 17,
    representatives: Mapping[str, str] | None = None,
    skip_same_class: bool = False,
) -> ClassKernTable:
    """Fit class-pair kerns so representative optical gaps hit ``target``.

    For every ordered pair of classes ``(A, B)``, picks a representative glyph
    from each (``representatives[class]`` or the class's first member), looks
    those glyphs up in ``glyphs``, and runs
    :func:`~typekernel.optics.space.fit_kern_pair`. Missing representatives
    skip that class pair.

    ``target`` may be a :class:`RhythmSpec`, a raw gap float, or ``None``
    (median self-gap of all available representatives).
    """
    from typekernel.optics.space import fit_kern_pair, pair_gap_optical

    classes_t = tuple(classes)
    if not classes_t:
        return ClassKernTable()

    reps: dict[str, str] = {}
    for kc in classes_t:
        if representatives and kc.name in representatives:
            reps[kc.name] = representatives[kc.name]
        else:
            reps[kc.name] = kc.representative
        if reps[kc.name] not in glyphs:
            # try any member present
            for m in kc.members:
                if m in glyphs:
                    reps[kc.name] = m
                    break

    available = {name: glyphs[name] for name in reps.values() if name in glyphs}
    if target is None:
        if not available:
            return ClassKernTable(classes_t, ())
        gaps = [
            pair_gap_optical(g, g, kern=0.0, samples=samples)
            for g in available.values()
        ]
        gaps.sort()
        target_gap = gaps[len(gaps) // 2]
        if target_gap <= 0:
            target_gap = 0.16 * next(iter(available.values())).context.x_height
    elif isinstance(target, RhythmSpec):
        target_gap = target.target_gap
    else:
        target_gap = float(target)

    pairs: list[ClassKernPair] = []
    for left_c in classes_t:
        for right_c in classes_t:
            if skip_same_class and left_c.name == right_c.name:
                continue
            ln = reps.get(left_c.name)
            rn = reps.get(right_c.name)
            if ln is None or rn is None:
                continue
            left_g = glyphs.get(ln)
            right_g = glyphs.get(rn)
            if left_g is None or right_g is None:
                continue
            value = fit_kern_pair(left_g, right_g, target_gap, samples=samples)
            pairs.append(ClassKernPair(left_c.name, right_c.name, value))
    return ClassKernTable(classes_t, tuple(pairs))


def default_latin_kern_classes() -> tuple[KernClass, ...]:
    """Starter lowercase shape classes for geometric Latin experiments."""
    return (
        KernClass("round", ("o", "c", "e")),
        KernClass("straight", ("n", "h", "i", "l", "u")),
        KernClass("diagonal", ("v", "w", "y", "x", "z", "a")),  # a often behaves open/diagonal
        KernClass("hook", ("j", "f", "t", "r")),
    )

def sidebearing_for_width(ctx: DesignContext, ink_width: float) -> float:
    """Heuristic sidebearing from context rhythm and glyph ink width."""
    sb = max(
        0.04 * ctx.units_per_em,
        ctx.sidebearing_ratio * ctx.x_height,
    )
    scale = ctx.x_height / max(ink_width, 1.0)
    scale = max(0.90, min(1.10, scale))
    return sb * scale


def layout_glyphs(
    glyphs: list[ComposedGlyph],
    names: list[str] | None = None,
    *,
    tracking: float | None = None,
    kerning: KernTable | None = None,
    origin_x: float = 0.0,
) -> list[float]:
    """Return pen-x positions for each glyph, applying tracking and kerning.

    If ``names`` is omitted, kerning is skipped (tracking still applies).
    """
    if not glyphs:
        return []
    ctx = glyphs[0].context
    track = ctx.tracking if tracking is None else tracking
    advances = [g.advance for g in glyphs]
    xs = layout_x_positions(advances, tracking=track, origin_x=origin_x)
    if kerning is None or names is None:
        return xs
    if len(names) != len(glyphs):
        raise ValueError("names length must match glyphs")
    # Rebuild with pairwise kern inserted between glyphs.
    out: list[float] = []
    x = origin_x
    for i, (g, name) in enumerate(zip(glyphs, names)):
        out.append(x)
        x += g.advance
        if i < len(glyphs) - 1:
            x += track
            x += kerning.lookup(name, names[i + 1])
    return out

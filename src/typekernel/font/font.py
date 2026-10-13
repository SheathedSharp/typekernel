"""Font — the glyph set, character map, kerning and features of one style.

This is what a type designer ships: not a word specimen but a named set of
glyphs with metrics, a cmap, spacing data and OpenType feature code. The
compile layer (:mod:`typekernel.compile`) serialises a :class:`Font` to UFO
and builds binaries from it; nothing here touches OpenType tables.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any

from typekernel.font.glyph import Component, Glyph, glyph_name_for_char, notdef_glyph, space_glyph
from typekernel.font.info import FontInfo
from typekernel.geo.outline import Outline
from typekernel.parts.compose import Anchor, ComposedGlyph
from typekernel.parts.context import DesignContext
from typekernel.parts.metrics import ClassKernTable, KernTable

__all__ = ["Font"]

KERN1_PREFIX = "public.kern1."
KERN2_PREFIX = "public.kern2."


@dataclass
class Font:
    """Mutable builder for one font style.

    Glyph order is insertion order (``.notdef`` is always exported first).
    Kerning keys are glyph names or ``public.kern1.*`` / ``public.kern2.*``
    group names, exactly as in a UFO.
    """

    info: FontInfo
    context: DesignContext | None = None
    _glyphs: dict[str, Glyph] = field(default_factory=dict)
    groups: dict[str, tuple[str, ...]] = field(default_factory=dict)
    kerning: dict[tuple[str, str], float] = field(default_factory=dict)
    features: str = ""

    @classmethod
    def from_context(
        cls,
        ctx: DesignContext,
        family_name: str,
        style_name: str = "Regular",
        *,
        space_width: float | None = None,
        **info_overrides: Any,
    ) -> Font:
        """New font with info derived from ``ctx`` plus ``.notdef`` and ``space``."""
        info = FontInfo.from_context(ctx, family_name, style_name, **info_overrides)
        font = cls(info=info, context=ctx)
        font.add_glyph(notdef_glyph(ctx))
        font.add_glyph(space_glyph(ctx, space_width))
        return font

    # --- glyphs -----------------------------------------------------------

    def add_glyph(self, glyph: Glyph, *, replace: bool = False) -> Glyph:
        """Add ``glyph``; raises on a name clash unless ``replace=True``."""
        if glyph.name in self._glyphs and not replace:
            raise ValueError(f"glyph {glyph.name!r} already exists (pass replace=True)")
        self._glyphs[glyph.name] = glyph
        return glyph

    def add_char(self, char: str, composed: ComposedGlyph, *, replace: bool = False) -> Glyph:
        """Add a parts-layer glyph for ``char`` (AGL name, ``ord(char)`` mapped)."""
        return self.add_glyph(Glyph.for_char(char, composed), replace=replace)

    def add_chars(
        self, glyphs: Mapping[str, ComposedGlyph], *, replace: bool = False
    ) -> list[Glyph]:
        """Add many ``{char: ComposedGlyph}`` entries at once."""
        return [self.add_char(ch, g, replace=replace) for ch, g in glyphs.items()]

    def add_composite(
        self,
        char: str,
        base: str,
        marks: tuple[tuple[str, str, str], ...],
        *,
        replace: bool = False,
    ) -> Glyph:
        """Build ``char`` from ``base`` plus mark glyphs aligned on anchors.

        Each mark entry is ``(mark_glyph_name, base_anchor, mark_anchor)``.
        Advance and anchors are taken from the base glyph.
        """
        if len(char) != 1:
            raise ValueError(f"expected one character, got {char!r}")
        base_name = self.resolve(base)
        if base_name is None:
            raise KeyError(f"unknown base glyph {base!r}")
        base_g = self._glyphs[base_name]

        def _anchor(g: Glyph, name: str) -> Anchor:
            for a in g.anchors:
                if a.name == name:
                    return a
            raise KeyError(f"glyph {g.name!r} has no anchor {name!r}")

        components: list[Component] = [Component(base_name)]
        for mark_name, base_anchor, mark_anchor in marks:
            if mark_name not in self._glyphs:
                raise KeyError(f"unknown mark glyph {mark_name!r}")
            mark_g = self._glyphs[mark_name]
            ba = _anchor(base_g, base_anchor)
            ma = _anchor(mark_g, mark_anchor)
            components.append(Component.offset(mark_name, ba.x - ma.x, ba.y - ma.y))

        glyph = Glyph(
            glyph_name_for_char(char),
            Outline(()),
            base_g.advance,
            unicodes=(ord(char),),
            anchors=base_g.anchors,
            components=tuple(components),
        )
        return self.add_glyph(glyph, replace=replace)

    def remove_glyph(self, name: str) -> None:
        del self._glyphs[name]

    def __getitem__(self, name: str) -> Glyph:
        return self._glyphs[name]

    def __contains__(self, name: object) -> bool:
        return name in self._glyphs

    def __iter__(self) -> Iterator[Glyph]:
        return iter(self._glyphs.values())

    def __len__(self) -> int:
        return len(self._glyphs)

    @property
    def glyph_order(self) -> list[str]:
        names = list(self._glyphs)
        if ".notdef" in self._glyphs:
            names.remove(".notdef")
            names.insert(0, ".notdef")
        return names

    def cmap(self) -> dict[int, str]:
        """Code point → glyph name (first glyph wins on duplicates)."""
        out: dict[int, str] = {}
        for g in self._glyphs.values():
            for cp in g.unicodes:
                out.setdefault(cp, g.name)
        return out

    def resolve(self, name: str) -> str | None:
        """Glyph name for ``name``: an existing glyph name, or a mapped character."""
        if name in self._glyphs:
            return name
        if len(name) == 1:
            return self.cmap().get(ord(name))
        return None

    # --- spacing ------------------------------------------------------------

    def add_kern_table(self, table: KernTable, *, strict: bool = False) -> list[str]:
        """Merge glyph-pair kerning. Names may be glyph names or characters.

        Pairs naming glyphs not in the font are skipped and returned (or raise
        ``KeyError`` when ``strict``), so starter tables can be larger than the
        current glyph set.
        """
        skipped: list[str] = []
        for pair in table.pairs:
            left, right = self.resolve(pair.left), self.resolve(pair.right)
            if left is None or right is None:
                missing = pair.left if left is None else pair.right
                if strict:
                    raise KeyError(f"kern pair names unknown glyph {missing!r}")
                skipped.append(missing)
                continue
            self.kerning[(left, right)] = pair.value
        return sorted(set(skipped))

    def add_class_kern_table(self, table: ClassKernTable, *, strict: bool = False) -> list[str]:
        """Merge class kerning as UFO ``public.kern1/kern2`` groups + group pairs.

        Members missing from the font are dropped (or raise when ``strict``);
        classes left empty are omitted. A glyph may sit in only one left and one
        right kerning group — overlaps raise ``ValueError``.
        """
        skipped: list[str] = []
        present: dict[str, tuple[str, ...]] = {}
        for kc in table.classes:
            resolved_members: list[str] = []
            for m in kc.members:
                resolved = self.resolve(m)
                if resolved is None:
                    if strict:
                        raise KeyError(f"kern class {kc.name!r} names unknown glyph {m!r}")
                    skipped.append(m)
                else:
                    resolved_members.append(resolved)
            if resolved_members:
                present[kc.name] = tuple(resolved_members)

        for prefix in (KERN1_PREFIX, KERN2_PREFIX):
            for name, members in present.items():
                self.groups[prefix + name] = members
            self._check_group_exclusive(prefix)

        for pair in table.pairs:
            if pair.left_class in present and pair.right_class in present:
                key = (KERN1_PREFIX + pair.left_class, KERN2_PREFIX + pair.right_class)
                self.kerning[key] = pair.value
        return sorted(set(skipped))

    def _check_group_exclusive(self, prefix: str) -> None:
        owner: dict[str, str] = {}
        for group, members in self.groups.items():
            if not group.startswith(prefix):
                continue
            for m in members:
                if m in owner and owner[m] != group:
                    raise ValueError(
                        f"glyph {m!r} is in two kerning groups: {owner[m]!r} and {group!r}"
                    )
                owner[m] = group

    # --- checks -------------------------------------------------------------

    def validate(self) -> list[str]:
        """Return problems that would break or corrupt a build (empty = OK)."""
        problems: list[str] = []
        if ".notdef" not in self._glyphs:
            problems.append("missing .notdef glyph")

        seen: dict[int, str] = {}
        for g in self._glyphs.values():
            for cp in g.unicodes:
                if cp in seen:
                    problems.append(f"U+{cp:04X} mapped by both {seen[cp]!r} and {g.name!r}")
                else:
                    seen[cp] = g.name
            if g.advance < 0:
                problems.append(f"glyph {g.name!r} has negative advance {g.advance}")
            for ci, contour in enumerate(g.outline.contours):
                if contour.segments and not contour.closed:
                    problems.append(f"glyph {g.name!r} contour {ci} is open")
            for comp in g.components:
                if comp.base not in self._glyphs:
                    problems.append(
                        f"glyph {g.name!r} references missing component {comp.base!r}"
                    )

        problems.extend(self._component_cycles())

        for group, members in self.groups.items():
            for m in members:
                if m not in self._glyphs:
                    problems.append(f"group {group!r} lists missing glyph {m!r}")
        for left, right in self.kerning:
            for side in (left, right):
                if side not in self._glyphs and side not in self.groups:
                    problems.append(f"kerning references unknown {side!r}")
        return problems

    def _component_cycles(self) -> list[str]:
        problems: list[str] = []
        state: dict[str, int] = {}  # 1 = visiting, 2 = done

        def visit(name: str, path: list[str]) -> None:
            if state.get(name) == 2 or name not in self._glyphs:
                return
            if state.get(name) == 1:
                cycle = path[path.index(name) :] + [name]
                problems.append("component cycle: " + " -> ".join(cycle))
                return
            state[name] = 1
            for comp in self._glyphs[name].components:
                visit(comp.base, path + [name])
            state[name] = 2

        for name in self._glyphs:
            visit(name, [])
        return problems

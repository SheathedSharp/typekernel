"""compose — build a Glyph from Composite + base/mark Glyphs (target §3.4)."""

from __future__ import annotations

from collections.abc import Mapping

from typekernel.font.glyph import Anchor, Component, Glyph
from typekernel.geo.outline import Outline
from typekernel.project.evaluate import unicodes_for_glyph_name
from typekernel.project.manifest import Composite

__all__ = ["compose"]


def compose(spec: Composite, glyphs: Mapping[str, Glyph], *, name: str) -> Glyph:
    """Align ``spec.marks`` onto ``spec.base`` using ``mark@anchor`` entries.

    Mark ``_<anchor>`` pairs with the current ``<anchor>`` position (base, then
    prior mark public anchors for mkmk). Advance and base anchors are inherited;
    non-underscore mark anchors are translated into the composite.
    """
    if spec.base not in glyphs:
        raise KeyError(f"unknown base glyph {spec.base!r}")
    base = glyphs[spec.base]

    components: list[Component] = [Component(spec.base)]
    # Live attachment positions in composite space.
    positions: dict[str, tuple[float, float]] = {a.name: (a.x, a.y) for a in base.anchors}
    out_anchors: dict[str, Anchor] = {a.name: a for a in base.anchors}

    for entry in spec.marks:
        if "@" not in entry:
            raise ValueError(
                f"composite mark entry {entry!r} must be 'markName@anchorName'"
            )
        mark_name, anchor = entry.split("@", 1)
        if mark_name not in glyphs:
            raise KeyError(f"unknown mark glyph {mark_name!r}")
        mark = glyphs[mark_name]
        attach = f"_{anchor}"
        if anchor not in positions:
            raise KeyError(
                f"no live anchor {anchor!r} while placing {mark_name!r} "
                f"(base={spec.base!r})"
            )
        mark_attach = next((a for a in mark.anchors if a.name == attach), None)
        if mark_attach is None:
            raise KeyError(f"mark {mark_name!r} has no attachment anchor {attach!r}")
        bx, by = positions[anchor]
        dx = bx - mark_attach.x
        dy = by - mark_attach.y
        components.append(Component.offset(mark_name, dx, dy))
        for a in mark.anchors:
            if a.name.startswith("_"):
                continue
            ax, ay = a.x + dx, a.y + dy
            positions[a.name] = (ax, ay)
            out_anchors[a.name] = Anchor(a.name, ax, ay)

    if spec.unicodes is None:
        unicodes = unicodes_for_glyph_name(name)
    else:
        unicodes = tuple(int(u) for u in spec.unicodes)

    return Glyph(
        name=name,
        outline=Outline(()),
        advance=base.advance,
        unicodes=unicodes,
        anchors=tuple(out_anchors.values()),
        components=tuple(components),
    )

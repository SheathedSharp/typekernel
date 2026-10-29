"""compose() aligns marks on base anchors (target §3.4)."""

from __future__ import annotations

from typekernel.font.glyph import Anchor, Glyph
from typekernel.geo.outline import Outline
from typekernel.project import Composite, compose


def _g(name: str, *, anchors: list[tuple[str, float, float]], advance: float = 100.0) -> Glyph:
    return Glyph(
        name=name,
        outline=Outline(()),
        advance=advance,
        anchors=tuple(Anchor(n, x, y) for n, x, y in anchors),
    )


def test_compose_offsets_mark_to_base_top() -> None:
    glyphs = {
        "base": _g("base", anchors=[("top", 50.0, 500.0)], advance=200.0),
        "acutecomb": _g("acutecomb", anchors=[("_top", 0.0, 0.0), ("top", 0.0, 80.0)]),
    }
    out = compose(
        Composite(base="base", marks=("acutecomb@top",), unicodes=(0x00E1,)),
        glyphs,
        name="aacute",
    )
    assert out.name == "aacute"
    assert out.advance == 200.0
    assert out.unicodes == (0x00E1,)
    assert len(out.components) == 2
    assert out.components[0].base == "base"
    assert out.components[1].base == "acutecomb"
    # mark _top (0,0) → base top (50,500) ⇒ dx=50, dy=500
    assert out.components[1].transform[4:] == (50.0, 500.0)
    # mark public top replaces live top (mkmk): (0,80)+(50,500)
    names = {a.name: (a.x, a.y) for a in out.anchors}
    assert names["top"] == (50.0, 580.0)


def test_compose_mkmk_stacks_on_prior_mark_anchor() -> None:
    glyphs = {
        "base": _g("base", anchors=[("top", 10.0, 100.0)]),
        "m1": _g("m1", anchors=[("_top", 0.0, 0.0), ("top", 0.0, 40.0)]),
        "m2": _g("m2", anchors=[("_top", 0.0, 0.0)]),
    }
    out = compose(
        Composite(base="base", marks=("m1@top", "m2@top")),
        glyphs,
        name="stack",
    )
    # first mark at (10,100); its public top becomes (10,140); second at that
    assert out.components[1].transform[4:] == (10.0, 100.0)
    assert out.components[2].transform[4:] == (10.0, 140.0)

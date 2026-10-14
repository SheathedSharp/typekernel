"""DesignContext knob reach — which glyphs must respond to each field."""

from __future__ import annotations

from dataclasses import replace

import pytest

from typekernel.parts import Controls, DesignContext


def _shape_changed(base: dict[str, object], other: dict[str, object]) -> list[str]:
    changed: list[str] = []
    for ch, a in base.items():
        b = other[ch]
        if type(a) is not type(b):
            changed.append(ch)
            continue
        from typekernel.parts.compose import ComposedGlyph

        assert isinstance(a, ComposedGlyph) and isinstance(b, ComposedGlyph)

        def pts(g: ComposedGlyph) -> list[tuple[float, float]]:
            out: list[tuple[float, float]] = []
            for o in (*g.solids, *g.holes):
                for ct in o.contours:
                    for seg in ct.segments:
                        out.extend((p.x, p.y) for p in seg.points)
            return out

        pa, pb = pts(a), pts(b)
        if len(pa) != len(pb):
            changed.append(ch)
            continue
        ax0, ay0 = pa[0]
        bx0, by0 = pb[0]
        diff = max(
            max(abs((x - ax0) - (u - bx0)), abs((y - ay0) - (v - by0)))
            for (x, y), (u, v) in zip(pa, pb)
        )
        if diff > 0.5:
            changed.append(ch)
    return changed


def _build(ctx: DesignContext) -> dict[str, object]:
    return Controls.from_context(ctx).build_all()


@pytest.mark.xfail(strict=True, reason="contrast should move all round letters (M3)")
def test_contrast_moves_round_letters() -> None:
    base = DesignContext.humanist_sans()
    a = _build(base)
    b = _build(base.tuned(contrast=0.5))
    round_letters = {"a", "b", "c", "d", "g", "i", "j", "l", "o", "p", "q", "C", "I", "O", "0"}
    changed = set(_shape_changed(a, b))
    still_static = round_letters - changed
    assert not still_static, sorted(still_static)


@pytest.mark.xfail(strict=True, reason="terminal_style should reach most terminals (M3)")
def test_terminal_style_reaches_many_glyphs() -> None:
    base = DesignContext.humanist_sans()
    a = _build(base)
    b = _build(replace(base, terminal_style="horizontal"))
    changed = _shape_changed(a, b)
    assert len(changed) >= 20

"""DesignContext knob reach — which glyphs must respond to each field."""

from __future__ import annotations

from dataclasses import replace

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


def test_contrast_moves_round_letters() -> None:
    base = DesignContext.humanist_sans()
    a = _build(base)
    b = _build(base.tuned(contrast=0.5))
    round_letters = {"a", "b", "c", "d", "g", "i", "j", "l", "o", "p", "q", "C", "I", "O", "0"}
    changed = set(_shape_changed(a, b))
    still_static = round_letters - changed
    assert not still_static, sorted(still_static)


def test_terminal_style_reaches_many_glyphs() -> None:
    base = DesignContext.humanist_sans()
    a = _build(base)
    b = _build(replace(base, terminal_style="horizontal"))
    changed = _shape_changed(a, b)
    assert len(changed) >= 20


def test_terminal_style_angled_reaches_open_stroke_glyphs() -> None:
    """TK-304: angled terminals move bowl / hook letters and cap ``F``/``T`` bar ends."""
    base = DesignContext.humanist_sans()
    a = _build(base)
    b = _build(replace(base, terminal_style="angled"))
    changed = _shape_changed(a, b)
    assert len(changed) >= 20
    assert {"F", "T", "k"}.issubset(set(changed))


def test_terminal_style_ball_reaches_open_stroke_glyphs() -> None:
    """TK-304: ball terminals on open strokes and cap bar ends."""
    base = DesignContext.humanist_sans()
    a = _build(base)
    b = _build(replace(base, terminal_style="ball"))
    changed = _shape_changed(a, b)
    assert len(changed) >= 20
    assert {"F", "T", "e"}.issubset(set(changed))


def test_terminal_style_flared_reaches_open_stroke_glyphs() -> None:
    """TK-304: flared terminals widen open stroke ends."""
    base = DesignContext.humanist_sans()
    a = _build(base)
    b = _build(replace(base, terminal_style="flared"))
    changed = _shape_changed(a, b)
    assert len(changed) >= 20
    assert {"F", "T", "c"}.issubset(set(changed))


def test_stress_moves_round_stroke_counters() -> None:
    """TK-302: stress rotates the thin point on bowl / ring glyphs."""
    ctx = DesignContext.geometric_sans().tuned(contrast=0.55, stem=90.0)
    probe = "ocCO0s235689"
    a = {ch: Controls.from_context(ctx).build(ch) for ch in probe}
    b = {ch: Controls.from_context(ctx.tuned(stress=25.0)).build(ch) for ch in probe}
    changed = set(_shape_changed(a, b))
    assert "o" in changed
    assert "s" in changed
    assert {"3", "6", "8"}.issubset(changed)
    assert len(changed) >= 6


def test_stress_reaches_many_glyphs_on_humanist() -> None:
    """TK-107 / appendix C: ``stress=25`` on ``humanist_sans`` moves many bowl/ring glyphs."""
    base = DesignContext.humanist_sans()
    a = _build(base)
    b = _build(base.tuned(stress=25.0))
    changed = _shape_changed(a, b)
    assert len(changed) >= 20
    assert {"o", "e", "c", "0"}.issubset(set(changed))

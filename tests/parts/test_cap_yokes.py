"""Public Usage A capital yokes — first wave H I L T E F O C V X A."""

from __future__ import annotations

import pytest

from typekernel.font import Font, Master, check_masters
from typekernel.geo.outline import bounds
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import (
    A_yoke,
    C_yoke,
    DesignContext,
    E_yoke,
    F_yoke,
    FormSources,
    GlyphAssembler,
    H_yoke,
    I_yoke,
    L_yoke,
    O_yoke,
    T_yoke,
    V_yoke,
    X_yoke,
    build_H,
    build_O,
    cap_o_metrics,
    h_cap_metrics,
)
from typekernel.parts.caps import (
    A_from_H,
    C_from_O,
    E_from_H,
    F_from_H,
    I_from_H,
    L_from_H,
    T_from_H,
    V_from_H,
    X_from_H,
)


WAVE = "HILTEFOCVXA"


@pytest.fixture
def ctx() -> DesignContext:
    return DesignContext.geometric_sans().tuned(
        stem=88.0, x_height=548.0, sidebearing_ratio=0.09
    )


def _pts(outline) -> tuple[tuple[float, float], ...]:
    return tuple(
        (round(p.x, 3), round(p.y, 3))
        for c in outline.contours
        for s in c.segments
        for p in s.points
    )


def _pack_h(ctx: DesignContext, outline, h):
    return GlyphAssembler(ctx).with_design(h).add(outline).build().solids[0]


def test_straight_cap_yokes_match_builders(ctx: DesignContext) -> None:
    h = h_cap_metrics(ctx)
    H = build_H(ctx, h)
    assert _pts(H.solids[0]) == _pts(_pack_h(ctx, H_yoke(ctx, metrics=h), h))
    assert _pts(I_from_H(H).solids[0]) == _pts(_pack_h(ctx, I_yoke(ctx, metrics=h), h))
    assert _pts(L_from_H(H).solids[0]) == _pts(_pack_h(ctx, L_yoke(ctx, metrics=h), h))
    assert _pts(E_from_H(H).solids[0]) == _pts(_pack_h(ctx, E_yoke(ctx, metrics=h), h))
    assert _pts(F_from_H(H).solids[0]) == _pts(_pack_h(ctx, F_yoke(ctx, metrics=h), h))
    assert _pts(T_from_H(H).solids[0]) == _pts(_pack_h(ctx, T_yoke(ctx, metrics=h), h))


def test_round_and_diagonal_cap_yokes_match_builders(ctx: DesignContext) -> None:
    h = h_cap_metrics(ctx)
    o = cap_o_metrics(ctx)
    H = build_H(ctx, h)
    O = build_O(ctx, o)
    assert _pts(C_from_O(O).solids[0]) == _pts(
        GlyphAssembler(ctx).with_design(o).add(C_yoke(ctx, metrics=o)).build().solids[0]
    )
    assert _pts(V_from_H(H).solids[0]) == _pts(_pack_h(ctx, V_yoke(ctx, metrics=h), h))
    assert _pts(X_from_H(H).solids[0]) == _pts(_pack_h(ctx, X_yoke(ctx, metrics=h), h))
    assert _pts(A_from_H(H).solids[0]) == _pts(_pack_h(ctx, A_yoke(ctx, metrics=h), h))
    # O: same topology (outer+counter segment counts)
    oy = O_yoke(ctx, metrics=o)
    assert [len(c.segments) for c in oy.contours] == [
        len(c.segments) for c in O.solids[0].contours
    ]


def test_cap_yoke_wave_on_cap_zones(ctx: DesignContext) -> None:
    h = h_cap_metrics(ctx)
    for name, fn in (
        ("H", H_yoke),
        ("I", I_yoke),
        ("L", L_yoke),
        ("T", T_yoke),
        ("E", E_yoke),
        ("F", F_yoke),
        ("V", V_yoke),
        ("X", X_yoke),
    ):
        _, y0, _, y1 = bounds(fn(ctx))
        assert y0 == pytest.approx(0.0, abs=0.5), name
        assert y1 == pytest.approx(h.cap_height, abs=0.5), name
    _, y0, _, y1 = bounds(O_yoke(ctx))
    assert y0 == pytest.approx(-ctx.overshoot, abs=0.5)
    assert y1 == pytest.approx(h.cap_height + ctx.overshoot, abs=0.5)


def test_v_x_crotches_sealed_on_cap_yokes(ctx: DesignContext) -> None:
    """Even-odd hairline gate at diagonal crotches (reuse LC truncate)."""

    def hairlines(outline, *, max_gap: float = 4.0) -> list[tuple[float, float]]:
        bad: list[tuple[float, float]] = []
        _, y0, _, y1 = bounds(outline)
        y = y0 + 1.0
        while y < y1 - 1.0:
            iv = ink_intervals_at_y([outline], y)
            for i in range(len(iv) - 1):
                gap = iv[i + 1][0] - iv[i][1]
                if 0.0 < gap < max_gap:
                    bad.append((y, gap))
                    break
            y += 1.0
        return bad

    for stem in (48.0, 88.0, 140.0, 180.0):
        tuned = ctx.tuned(stem=stem)
        assert hairlines(V_yoke(tuned)) == [], stem
        assert hairlines(X_yoke(tuned)) == [], stem
        assert hairlines(A_yoke(tuned)) == [], stem


def test_cap_yoke_wave_interpolates_across_stems() -> None:
    ctx = DesignContext.humanist_sans()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        tuned = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "CapWave", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(tuned.derive(WAVE))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_form_sources_wave_uses_yoked_builders(ctx: DesignContext) -> None:
    drawn = FormSources.from_context(ctx).derive(WAVE)
    assert set(drawn) == set(WAVE)
    assert len(drawn["H"].solids[0].contours) == 1
    assert len(drawn["O"].solids[0].contours) == 2
    assert len(drawn["A"].solids[0].contours) == 2

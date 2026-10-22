"""Public Usage A capital yokes — full A–Z."""

from __future__ import annotations

import pytest

from typekernel.font import Font, Master, check_masters
from typekernel.geo.outline import bounds
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import (
    A_yoke,
    B_yoke,
    C_yoke,
    D_yoke,
    DesignContext,
    E_yoke,
    F_yoke,
    FormSources,
    G_yoke,
    GlyphAssembler,
    H_yoke,
    I_yoke,
    J_yoke,
    K_yoke,
    L_yoke,
    M_yoke,
    N_yoke,
    O_yoke,
    P_yoke,
    Q_yoke,
    R_yoke,
    S_yoke,
    T_yoke,
    U_yoke,
    V_yoke,
    W_yoke,
    X_yoke,
    Y_yoke,
    Z_yoke,
    build_H,
    build_O,
    cap_o_metrics,
    h_cap_metrics,
)
from typekernel.parts.caps import (
    A_from_H,
    B_from_H,
    C_from_O,
    D_from_H,
    E_from_H,
    F_from_H,
    G_from_O,
    I_from_H,
    J_from_H,
    K_from_H,
    L_from_H,
    M_from_H,
    N_from_H,
    P_from_H,
    Q_from_O,
    R_from_H,
    S_from_O,
    T_from_H,
    U_from_H,
    V_from_H,
    W_from_H,
    X_from_H,
    Y_from_H,
    Z_from_H,
)

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


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


def _pack(ctx: DesignContext, outline, design):
    return GlyphAssembler(ctx).with_design(design).add(outline).build().solids[0]


def test_all_cap_yokes_match_builders(ctx: DesignContext) -> None:
    h = h_cap_metrics(ctx)
    o = cap_o_metrics(ctx)
    H, O = build_H(ctx, h), build_O(ctx, o)
    cases = [
        ("A", A_from_H(H), A_yoke(ctx, metrics=h), h),
        ("B", B_from_H(H, O), B_yoke(ctx, metrics=h, o_metrics_rec=o), h),
        ("C", C_from_O(O), C_yoke(ctx, metrics=o), o),
        ("D", D_from_H(H, O), D_yoke(ctx, metrics=h, o_metrics_rec=o), h),
        ("E", E_from_H(H), E_yoke(ctx, metrics=h), h),
        ("F", F_from_H(H), F_yoke(ctx, metrics=h), h),
        ("G", G_from_O(O, H), G_yoke(ctx, metrics=o, h_metrics=h), o),
        ("H", H, H_yoke(ctx, metrics=h), h),
        ("I", I_from_H(H), I_yoke(ctx, metrics=h), h),
        ("J", J_from_H(H, O), J_yoke(ctx, metrics=h, o_metrics_rec=o), h),
        ("K", K_from_H(H), K_yoke(ctx, metrics=h), h),
        ("L", L_from_H(H), L_yoke(ctx, metrics=h), h),
        ("M", M_from_H(H), M_yoke(ctx, metrics=h), h),
        ("N", N_from_H(H), N_yoke(ctx, metrics=h), h),
        ("P", P_from_H(H, O), P_yoke(ctx, metrics=h, o_metrics_rec=o), h),
        ("Q", Q_from_O(O, H), Q_yoke(ctx, metrics=o, h_metrics=h), o),
        ("R", R_from_H(H, O), R_yoke(ctx, metrics=h, o_metrics_rec=o), h),
        ("S", S_from_O(O), S_yoke(ctx, metrics=o), o),
        ("T", T_from_H(H), T_yoke(ctx, metrics=h), h),
        ("U", U_from_H(H, O), U_yoke(ctx, metrics=h, o_metrics_rec=o), h),
        ("V", V_from_H(H), V_yoke(ctx, metrics=h), h),
        ("W", W_from_H(H), W_yoke(ctx, metrics=h), h),
        ("X", X_from_H(H), X_yoke(ctx, metrics=h), h),
        ("Y", Y_from_H(H), Y_yoke(ctx, metrics=h), h),
        ("Z", Z_from_H(H), Z_yoke(ctx, metrics=h), h),
    ]
    for name, built, yoke_ol, design in cases:
        assert _pts(built.solids[0]) == _pts(_pack(ctx, yoke_ol, design)), name
    # O topology
    oy = O_yoke(ctx, metrics=o)
    assert [len(c.segments) for c in oy.contours] == [
        len(c.segments) for c in O.solids[0].contours
    ]


def test_cap_yokes_on_cap_zones(ctx: DesignContext) -> None:
    h = h_cap_metrics(ctx)
    flat = {
        "H": H_yoke,
        "I": I_yoke,
        "L": L_yoke,
        "T": T_yoke,
        "E": E_yoke,
        "F": F_yoke,
        "V": V_yoke,
        "X": X_yoke,
        "Z": Z_yoke,
        "K": K_yoke,
        "M": M_yoke,
        "N": N_yoke,
        "W": W_yoke,
        "Y": Y_yoke,
    }
    for name, fn in flat.items():
        _, y0, _, y1 = bounds(fn(ctx))
        assert y0 == pytest.approx(0.0, abs=0.5), name
        assert y1 == pytest.approx(h.cap_height, abs=0.5), name
    _, y0, _, y1 = bounds(O_yoke(ctx))
    assert y0 == pytest.approx(-ctx.overshoot, abs=0.5)
    assert y1 == pytest.approx(h.cap_height + ctx.overshoot, abs=0.5)


def test_diagonal_cap_crotches_sealed(ctx: DesignContext) -> None:
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
        for name, fn in (
            ("V", V_yoke),
            ("W", W_yoke),
            ("X", X_yoke),
            ("A", A_yoke),
            ("K", K_yoke),
            ("Y", Y_yoke),
        ):
            assert hairlines(fn(tuned)) == [], f"{name} stem={stem}"


def test_full_cap_alphabet_interpolates_across_stems() -> None:
    ctx = DesignContext.humanist_sans()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        tuned = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "CapsAZ", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(tuned.derive(ALPHABET))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_form_sources_full_alphabet(ctx: DesignContext) -> None:
    drawn = FormSources.from_context(ctx).derive(ALPHABET)
    assert set(drawn) == set(ALPHABET)

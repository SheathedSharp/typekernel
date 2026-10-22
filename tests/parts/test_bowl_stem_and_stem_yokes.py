"""Bowl–stem spring seal + public i/l/o/f/t yokes."""

from __future__ import annotations

from typekernel.geo.joins import classify_joins
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import (
    DesignContext,
    GlyphAssembler,
    a_from_o,
    a_yoke,
    bowl_stem_yoke,
    build_n,
    build_o,
    d_from_o,
    f_from_n,
    f_yoke,
    i_from_n,
    i_yoke,
    l_from_n,
    l_yoke,
    o_yoke,
    t_from_n,
    t_yoke,
)
from typekernel.qa.lint import lint_glyph


def _ctx() -> DesignContext:
    return DesignContext.geometric_sans().tuned(
        stem=88.0, x_height=548.0, sidebearing_ratio=0.09
    )


def _hairlines(outline, *, max_gap: float = 3.0) -> list[tuple[float, float]]:
    bad: list[tuple[float, float]] = []
    y = -20.0
    while y <= 800.0:
        iv = ink_intervals_at_y([outline], y)
        for i in range(len(iv) - 1):
            gap = iv[i + 1][0] - iv[i][1]
            if 0.0 < gap < max_gap:
                bad.append((y, gap))
                break
        y += 1.0
    return bad


def _bad(glyph, ctx, name: str) -> list[str]:
    return [
        i.rule
        for i in lint_glyph(glyph, ctx, glyph_name=name)
        if i.rule in ("R1_winding", "R2_keyhole", "R3_self_intersect")
    ]


def test_a_and_bowl_stem_spring_sealed() -> None:
    ctx = _ctx()
    for ol in (a_yoke(ctx), bowl_stem_yoke(ctx), d_from_o(build_o(ctx), build_n(ctx)).solids[0]):
        jc = classify_joins(ol)
        assert jc.corners == 0
        assert jc.kinks == 0
        assert _hairlines(ol) == []


def test_a_from_o_matches_sealed_yoke_quality() -> None:
    ctx = _ctx()
    g = a_from_o(build_o(ctx), build_n(ctx), ctx)
    assert _hairlines(g.solids[0]) == []
    assert _bad(g, ctx, "a") == []


def test_stem_yokes_are_continuous_and_lint_clean() -> None:
    ctx = _ctx()
    cases = [
        ("i", i_yoke(ctx), 1),
        ("l", l_yoke(ctx), 1),
        ("o", o_yoke(ctx), 2),
        ("f", f_yoke(ctx, arm=0.82), 1),
        ("t", t_yoke(ctx, arm=0.58), 1),
    ]
    for name, ol, ncont in cases:
        assert len(ol.contours) == ncont
        g = GlyphAssembler(ctx).add(ol).build()
        assert _bad(g, ctx, name) == []


def test_ilft_yokes_match_builder_topology() -> None:
    """Public yokes share contour/segment counts with the letter builders."""
    ctx = _ctx()
    n = build_n(ctx)
    pairs = [
        (i_yoke(ctx), i_from_n(n, ctx).solids[0]),
        (l_yoke(ctx), l_from_n(n, ctx).solids[0]),
        (f_yoke(ctx, arm=0.82), f_from_n(n, ctx, arm=0.82).solids[0]),
        (t_yoke(ctx, arm=0.58), t_from_n(n, ctx, arm=0.58).solids[0]),
    ]
    for yoke, built in pairs:
        assert len(yoke.contours) == len(built.contours)
        assert len(yoke.contours[0].segments) == len(built.contours[0].segments)



def test_j_and_g_yokes_continuous_and_sealed() -> None:
    ctx = _ctx()
    from typekernel.parts import g_from_o, g_yoke, j_from_n, j_yoke, tittle

    j_body = j_yoke(ctx)
    assert len(j_body.contours) == 1
    assert classify_joins(j_body).kinks == 0
    j = (
        GlyphAssembler(ctx)
        .add(j_body)
        .add(tittle(ctx, ctx.stem / 2.0, ctx.x_height + ctx.stem * 0.55, size=ctx.stem * 0.95))
        .build()
    )
    assert _bad(j, ctx, "j") == []
    assert len(j_from_n(build_n(ctx), ctx).solids) == 2

    gy = g_yoke(ctx)
    assert len(gy.contours) == 2
    jc = classify_joins(gy)
    # Hook tip may keep a single 180° corner; post-shear blend
    # was removed so segment counts stay VF-fixed across stems.
    assert jc.corners <= 1
    assert jc.kinks == 0
    assert _hairlines(gy, max_gap=3.0) == []
    g = g_from_o(build_o(ctx), build_n(ctx), ctx)
    assert _hairlines(g.solids[0], max_gap=3.0) == []
    assert _bad(g, ctx, "g") == []


def test_overlap_seals_fine_bowl_stem_spring() -> None:
    """Fine y-grid near the upper join must not show a sub-5 even-odd slit."""
    ctx = _ctx()
    ol = a_yoke(ctx)
    bad: list[tuple[float, float]] = []
    y = ctx.x_height - ctx.stem * 0.5
    while y <= ctx.x_height - 5.0:
        iv = ink_intervals_at_y([ol], y)
        for i in range(len(iv) - 1):
            gap = iv[i + 1][0] - iv[i][1]
            if 0.0 < gap < 5.0:
                bad.append((y, gap))
                break
        y += 0.1
    assert bad == []

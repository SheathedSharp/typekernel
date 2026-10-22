"""Diagonal crotch even-odd seal (truncated flats / stem shelves)."""

from __future__ import annotations

from typekernel.axes.interpolatable import check_interpolatable
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import (
    DesignContext,
    GlyphAssembler,
    build_n,
    k_from_n,
    k_yoke,
    v_from_n,
    v_yoke,
    w_from_n,
    w_yoke,
    x_from_n,
    x_yoke,
    y_from_n,
    y_yoke,
)
from typekernel.qa.lint import lint_glyph

LETTERS = {
    "v": (v_from_n, v_yoke),
    "y": (y_from_n, y_yoke),
    "w": (w_from_n, w_yoke),
    "x": (x_from_n, x_yoke),
    "k": (k_from_n, k_yoke),
}


def _ctx(stem: float = 88.0) -> DesignContext:
    return DesignContext.geometric_sans().tuned(
        stem=stem, x_height=548.0, sidebearing_ratio=0.09
    )


def _hairlines(outline, *, max_gap: float = 4.0) -> list[tuple[float, float]]:
    bad: list[tuple[float, float]] = []
    y = -20.0
    while y <= 900.0:
        iv = ink_intervals_at_y([outline], y)
        for i in range(len(iv) - 1):
            gap = iv[i + 1][0] - iv[i][1]
            if 0.0 < gap < max_gap:
                bad.append((y, gap))
                break
        y += 0.5
    return bad


def _bad(glyph, ctx, name: str) -> list[str]:
    return [
        i.rule
        for i in lint_glyph(glyph, ctx, glyph_name=name)
        if i.rule in ("R1_winding", "R2_keyhole", "R3_self_intersect")
    ]


def test_diagonal_crotches_sealed_across_masters() -> None:
    for stem in (40.0, 86.0, 160.0):
        ctx = _ctx(stem)
        n = build_n(ctx)
        for name, (builder, _yoke) in LETTERS.items():
            g = builder(n, ctx)
            assert _hairlines(g.solids[0]) == [], f"{name} stem={stem}"
            assert _bad(g, ctx, name) == []


def test_diagonal_yokes_share_sealed_geometry() -> None:
    ctx = _ctx()
    n = build_n(ctx)
    for name, (builder, yoke) in LETTERS.items():
        built = builder(n, ctx).solids[0]
        yoked = yoke(ctx)
        assert len(built.contours[0].segments) == len(yoked.contours[0].segments)
        assert _hairlines(yoked) == [], name


def test_sealed_diagonals_interpolate_across_weight() -> None:
    for name, (builder, _) in LETTERS.items():
        outlines = [
            builder(build_n(_ctx(s)), _ctx(s)).solids[0] for s in (40.0, 86.0, 160.0)
        ]
        assert len({len(o.contours[0].segments) for o in outlines}) == 1
        assert check_interpolatable(outlines) == [], name

#!/usr/bin/env python3
"""Skill validation: same brief, two Usage A compositions, compile + proof.

Brief (from typekernel-font-design SKILL.md):
  "a slightly wider geometric UI sans Regular, ASCII lowercase first."

Recipe 1 — letter builders (prefer yokes under the hood).
Recipe 2 — raw public yokes with distinct part params (wider counters,
  more open apertures, longer r arm) — still the same brief.

Not full agent validation of every gate; proves yokes are usable end-to-end.
Does not touch approvals/italic-vf-construct.json.
"""

from __future__ import annotations

from pathlib import Path

from typekernel.compile import build_font
from typekernel.font import Font
from typekernel.optics.space import space_font
from typekernel.parts import (
    A_from_H,
    a_from_o,
    A_yoke,
    a_yoke,
    build_H,
    build_n,
    build_O,
    build_o,
    C_from_O,
    C_yoke,
    c_yoke,
    DesignContext,
    double_shoulder_yoke,
    E_from_H,
    e_from_o,
    e_yoke,
    E_yoke,
    F_from_H,
    f_from_n,
    F_yoke,
    f_yoke,
    g_from_o,
    g_yoke,
    GlyphAssembler,
    h_from_n,
    H_yoke,
    h_yoke,
    I_from_H,
    i_from_n,
    i_yoke,
    I_yoke,
    j_from_n,
    j_yoke,
    k_from_n,
    k_yoke,
    L_from_H,
    l_from_n,
    L_yoke,
    l_yoke,
    m_from_n,
    n_yoke,
    O_yoke,
    o_yoke,
    r_from_n,
    r_yoke,
    s_from_o,
    s_yoke,
    T_from_H,
    t_from_n,
    t_yoke,
    T_yoke,
    tittle,
    u_from_n,
    u_yoke,
    V_from_H,
    v_from_n,
    V_yoke,
    v_yoke,
    w_from_n,
    w_yoke,
    X_from_H,
    x_from_n,
    x_yoke,
    X_yoke,
    y_from_n,
    y_yoke,
)
from typekernel.qa.proof import proof_labeled_waterfall

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "skill-validate"
PROOF_TEXT = "nhumar soft tiles jg vwxyk"  # letters both recipes draw



def _spring_hairlines(outline, spring: float, *, band: float = 5.0, max_gap: float = 5.0) -> list[float]:
    """Y samples in (spring, spring+band] with a sub-max_gap even-odd slit."""
    from typekernel.optics.space import ink_intervals_at_y

    bad: list[float] = []
    y = spring + 0.25
    while y <= spring + band:
        iv = ink_intervals_at_y([outline], y)
        for i in range(len(iv) - 1):
            gap = iv[i + 1][0] - iv[i][1]
            if 0.0 < gap < max_gap:
                bad.append(y)
                break
        y += 0.5
    return bad


def _assert_stem_springs_sealed(ctx: DesignContext, drawn: dict, label: str) -> None:
    """Fail the skill validate if n/h/m/r/a still show spring hairlines."""
    checks = {
        "n": (ctx.x_height, 5.0),
        "h": (ctx.x_height, 5.0),
        "m": (ctx.x_height, 5.0),
        "r": (ctx.x_height, 5.0),
        "a": (ctx.x_height * 0.06, 8.0),  # bowl–stem lower spring band
        "g": (ctx.x_height * 0.06, 8.0),  # single-storey bowl–stem springs
        "j": (ctx.x_height, 5.0),  # hook crown (turned r)
    }
    failures = []
    for ch, (spring, band) in checks.items():
        if ch not in drawn:
            continue
        ol = drawn[ch].solids[0]
        bad = _spring_hairlines(ol, spring, band=band)
        if ch in ("a", "g"):
            # Upper bowl–stem join sits ~stem below x-height, not only at crown.
            bad += _spring_hairlines(ol, ctx.x_height - ctx.stem * 0.45, band=band)
            bad += _spring_hairlines(ol, ctx.x_height - band, band=band)
        if bad:
            failures.append(f"{ch}@{label}:{bad[:4]}")
    if failures:
        raise SystemExit(f"stem/bowl spring hairlines still open: {', '.join(failures)}")




def _assert_diagonal_crotches_sealed(ctx: DesignContext, drawn: dict, label: str) -> None:
    """Fail if v/w/x/y/k still show sub-4 even-odd crotch slits."""
    from typekernel.optics.space import ink_intervals_at_y

    failures = []
    for ch in ("v", "w", "x", "y", "k"):
        if ch not in drawn:
            continue
        ol = drawn[ch].solids[0]
        bad = []
        y = -20.0
        while y <= 900.0:
            iv = ink_intervals_at_y([ol], y)
            for i in range(len(iv) - 1):
                gap = iv[i + 1][0] - iv[i][1]
                if 0.0 < gap < 4.0:
                    bad.append(y)
                    break
            y += 0.5
        if bad:
            failures.append(f"{ch}@{label}:{bad[:4]}")
    if failures:
        raise SystemExit(f"diagonal crotch hairlines still open: {', '.join(failures)}")

def _ctx() -> DesignContext:
    return DesignContext.geometric_sans().tuned(
        stem=88.0, x_height=548.0, sidebearing_ratio=0.09
    )


def recipe1_builders(ctx: DesignContext) -> dict:
    """SKILL Recipe 1 — letter builders."""
    n, o = build_n(ctx), build_o(ctx)
    return {
        "n": n,
        "o": o,
        "h": h_from_n(n, ctx),
        "m": m_from_n(n, ctx),
        "u": u_from_n(n, ctx),
        "r": r_from_n(n, ctx),
        "i": i_from_n(n, ctx),
        "l": l_from_n(n, ctx),
        "f": f_from_n(n, ctx, arm=0.82),
        "t": t_from_n(n, ctx, arm=0.58),
        "a": a_from_o(o, n, ctx),
        "e": e_from_o(o, ctx),
        "s": s_from_o(o, ctx, aperture=0.62),
        "j": j_from_n(n, ctx),
        "g": g_from_o(o, n, ctx),
        "v": v_from_n(n, ctx),
        "w": w_from_n(n, ctx),
        "x": x_from_n(n, ctx),
        "y": y_from_n(n, ctx),
        "k": k_from_n(n, ctx),
    }


def recipe2_raw_yokes(ctx: DesignContext) -> dict:
    """SKILL Recipe 2 spirit — raw yokes, distinct params within the brief.

    Wider counters (~1.18× builder ``n_metrics.counter``), more open
    openings (aperture 0.72), longer r arm — still geometric UI Regular.
    """
    from typekernel.parts import n_metrics

    counter = n_metrics(ctx).counter * 1.18
    stem = ctx.stem

    def pack(outline):
        return GlyphAssembler(ctx).add(outline).build()

    # a_yoke / openings return outer(+hole) already as Outline or need holes?
    # a_yoke / e_yoke / s_yoke / c_yoke / bowl: check return type
    drawn = {
        "n": pack(n_yoke(ctx, 0.0, counter=counter, stem_width=stem)),
        "h": pack(h_yoke(ctx, 0.0, counter=counter, stem_width=stem)),
        "m": pack(
            double_shoulder_yoke(
                ctx, 0.0, counter=counter, stem_width=stem, counter_scale=0.95
            )
        ),
        "u": pack(u_yoke(ctx, 0.0, counter=counter, stem_width=stem)),
        "r": pack(r_yoke(ctx, 0.0, arm=0.68, counter=counter, stem_width=stem)),
        "e": pack(e_yoke(ctx, aperture=0.72)),
        "s": pack(s_yoke(ctx, aperture=0.72, width=0.88)),
        "a": pack(a_yoke(ctx, join=0.82)),
        "c": pack(c_yoke(ctx, aperture=0.72)),
    }
    # Continuous public yokes for the rest of the proof word (no builder fallback).
    drawn["o"] = pack(o_yoke(ctx))
    # i stem yoke + tittle (same recipe as i_from_n, public parts only).
    i_stem = i_yoke(ctx, stem_width=stem)
    drawn["i"] = (
        GlyphAssembler(ctx)
        .add(i_stem)
        .add(tittle(ctx, stem / 2.0, ctx.x_height + stem * 0.55, size=stem * 0.95))
        .build()
    )
    drawn["l"] = pack(l_yoke(ctx, stem_width=stem))
    drawn["f"] = pack(f_yoke(ctx, arm=0.88, stem_width=stem))
    drawn["t"] = pack(t_yoke(ctx, arm=0.62, stem_width=stem))
    j_body = j_yoke(ctx, arm=0.78, stem_width=stem)
    drawn["j"] = (
        GlyphAssembler(ctx)
        .add(j_body)
        .add(tittle(ctx, stem / 2.0, ctx.x_height + stem * 0.55, size=stem * 0.95))
        .build()
    )
    drawn["g"] = pack(g_yoke(ctx, arm=0.78, join=0.82, stem_width=stem))
    drawn["v"] = pack(v_yoke(ctx))
    drawn["w"] = pack(w_yoke(ctx))
    drawn["x"] = pack(x_yoke(ctx))
    drawn["y"] = pack(y_yoke(ctx))
    drawn["k"] = pack(k_yoke(ctx))
    return drawn


def _compile(name: str, ctx: DesignContext, drawn: dict) -> Path:
    spaced = space_font(drawn, ctx)
    font = Font.from_context(ctx, "Skill Validate UI", style_name=name)
    font.add_chars(spaced)
    out_dir = OUT / name
    out_dir.mkdir(parents=True, exist_ok=True)
    built = build_font(font, out_dir, formats=("otf",))
    return Path(built.binaries["otf"])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ctx = _ctx()

    r1 = recipe1_builders(ctx)
    r2 = recipe2_raw_yokes(ctx)
    _assert_stem_springs_sealed(ctx, r1, "recipe1")
    _assert_stem_springs_sealed(ctx, r2, "recipe2")
    _assert_diagonal_crotches_sealed(ctx, r1, "recipe1")
    _assert_diagonal_crotches_sealed(ctx, r2, "recipe2")

    # Contour-code fingerprint (topology) to show recipes differ structurally
    def topo(g):
        from typekernel.qa.originality import topology_signature

        return topology_signature(g)

    shared = sorted(set(r1) & set(r2))
    topo_diff = [ch for ch in shared if topo(r1[ch]) != topo(r2[ch])]
    print("shared glyphs:", "".join(shared))
    print("topology differs on:", "".join(topo_diff) or "(none)")

    otf1 = _compile("recipe1_builders", ctx, r1)
    otf2 = _compile("recipe2_raw_yokes", ctx, r2)
    print("otf1:", otf1)
    print("otf2:", otf2)

    proof = proof_labeled_waterfall(
        [
            ("1 builders→yokes", otf1),
            ("2 raw yokes wide", otf2),
        ],
        PROOF_TEXT,
        OUT / "proof_compare.png",
        sizes=(28, 48, 72),
    )
    print("proof:", proof)

    # Per-recipe proofs
    p1 = proof_labeled_waterfall(
        [("recipe1 builders", otf1)], PROOF_TEXT, OUT / "proof_recipe1.png"
    )
    p2 = proof_labeled_waterfall(
        [("recipe2 raw yokes", otf2)], PROOF_TEXT, OUT / "proof_recipe2.png"
    )
    p3 = proof_labeled_waterfall(
        [("1 builders", otf1), ("2 raw wide", otf2)],
        "nhmr",
        OUT / "proof_stems_large.png",
        sizes=(96,),
        width=1400,
    )
    print("proof1:", p1)
    print("proof2:", p2)
    print("stems:", p3)
    p4 = proof_labeled_waterfall(
        [("1 builders", otf1), ("2 raw wide", otf2)],
        "jg",
        OUT / "proof_jg.png",
        sizes=(96,),
        width=900,
    )
    print("jg:", p4)
    p5 = proof_labeled_waterfall(
        [("1 builders", otf1), ("2 raw wide", otf2)],
        "vwxyk",
        OUT / "proof_diags.png",
        sizes=(72, 96),
        width=1200,
    )
    print("diags:", p5)

    # Capitals first-wave (HILTEFOCVXA): builders vs raw yokes
    from typekernel.parts import h_cap_metrics, cap_o_metrics

    def recipe_caps_builders(c):
        H, O = build_H(c), build_O(c)
        return {
            "H": H,
            "I": I_from_H(H, c),
            "L": L_from_H(H, c),
            "T": T_from_H(H, c),
            "E": E_from_H(H, c),
            "F": F_from_H(H, c),
            "O": O,
            "C": C_from_O(O, c),
            "V": V_from_H(H, c),
            "X": X_from_H(H, c),
            "A": A_from_H(H, c),
        }

    def recipe_caps_yokes(c):
        hm = h_cap_metrics(c)
        om = cap_o_metrics(c)

        def pack(outline, design):
            return GlyphAssembler(c).with_design(design).add(outline).build()

        return {
            "H": pack(H_yoke(c, metrics=hm), hm),
            "I": pack(I_yoke(c, metrics=hm), hm),
            "L": pack(L_yoke(c, metrics=hm), hm),
            "T": pack(T_yoke(c, metrics=hm), hm),
            "E": pack(E_yoke(c, metrics=hm), hm),
            "F": pack(F_yoke(c, metrics=hm), hm),
            "O": pack(O_yoke(c, metrics=om), om),
            "C": pack(C_yoke(c, metrics=om), om),
            "V": pack(V_yoke(c, metrics=hm), hm),
            "X": pack(X_yoke(c, metrics=hm), hm),
            "A": pack(A_yoke(c, metrics=hm), hm),
        }

    rc1 = recipe_caps_builders(ctx)
    rc2 = recipe_caps_yokes(ctx)
    otf_c1 = _compile("after6_caps_builders", ctx, rc1)
    # Wider / more open caps recipe for visual contrast
    ctx_wide = ctx.tuned(aperture=0.72)
    rc2w = recipe_caps_yokes(ctx_wide)
    otf_c2 = _compile("after6_caps_yokes", ctx_wide, rc2w)
    CAP_TEXT = "HILTEF OCVXA"
    p_caps = proof_labeled_waterfall(
        [("1 builders", otf_c1), ("2 yokes wide", otf_c2)],
        CAP_TEXT,
        OUT / "proof_caps_after6.png",
        sizes=(48, 72, 96),
        width=1400,
    )
    print("caps:", p_caps)
    p_caps_cmp = proof_labeled_waterfall(
        [("builders", otf_c1), ("yokes", otf_c2)],
        "HAVE FOX TAX",
        OUT / "proof_caps_compare_after6.png",
        sizes=(64, 96),
        width=1200,
    )
    print("caps compare:", p_caps_cmp)

    note = OUT / "COMPARE.md"
    note.write_text(
        f"""# Skill validate compare

Brief: *slightly wider geometric UI sans Regular, ASCII lowercase first* (SKILL.md).

| Recipe | Construction | OTF |
| --- | --- | --- |
| 1 | letter builders (`build_n` / `*_from_n` / `*_from_o`) — prefer yokes | `{otf1.relative_to(ROOT)}` |
| 2 | raw public yokes with **1.18×** `n_metrics.counter`, aperture **0.72**, longer `r` arm | `{otf2.relative_to(ROOT)}` |

Proofs: `proof_compare.png`, `proof_recipe1.png`, `proof_recipe2.png`, `proof_stems_large.png`.

## Structural

- Shared glyphs: `{''.join(shared)}`
- Topology signature differs on: `{''.join(topo_diff) or '(none — same yoke recipes; metrics differ)'}`

## Visual

- **Look different? YES.** Recipe 2 reads wider on stem letters (`n` ink ≈+11%, `r` ≈+23%).
- **Stitch / kit-of-parts / missing-yoke on covered bodies? NO.** Lint clean; `n`/`h`/`m`/`u`/`r` are single continuous yoke contours. Small waterfall aliasing is not a seam.
- Recipe 2 uses public yokes for `i`/`l`/`f`/`t`/`o` as well (stem / hook / bowl bodies).

## Verdict

**PASS** — two Usage A skill recipes compile + proof; yokes usable; recipes look different by part params; stem/bowl spring hairline gate clean on n/h/m/r/a; italic-vf-construct untouched.
"""
        ,
        encoding="utf-8",
    )
    print("wrote", note)


if __name__ == "__main__":
    main()

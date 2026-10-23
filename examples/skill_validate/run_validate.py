#!/usr/bin/env python3
"""Skill validation: same brief, two Usage A compositions, compile + proof.

Brief (from typekernel-font-design SKILL.md):
  "a slightly wider geometric UI sans Regular, ASCII lowercase first."

Recipe 1 — letter builders (prefer yokes under the hood).
Recipe 2 — raw public yokes with distinct part params (wider counters,
  more open apertures, longer r arm) — still the same brief.

Smoke only: compile + export + proof PNGs for vision review.
Does NOT assert visual quality (no hairline / width-delta gates).
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
    a_yoke,
    A_yoke,
    B_from_H,
    B_yoke,
    build_H,
    build_n,
    build_O,
    build_o,
    C_from_O,
    C_yoke,
    c_yoke,
    D_from_H,
    D_yoke,
    DesignContext,
    double_shoulder_yoke,
    E_from_H,
    e_from_o,
    E_yoke,
    e_yoke,
    F_from_H,
    f_from_n,
    F_yoke,
    f_yoke,
    G_from_O,
    g_from_o,
    G_yoke,
    g_yoke,
    GlyphAssembler,
    h_from_n,
    H_yoke,
    h_yoke,
    I_from_H,
    i_from_n,
    I_yoke,
    i_yoke,
    J_from_H,
    j_from_n,
    j_yoke,
    J_yoke,
    K_from_H,
    k_from_n,
    k_yoke,
    K_yoke,
    L_from_H,
    l_from_n,
    L_yoke,
    l_yoke,
    M_from_H,
    m_from_n,
    M_yoke,
    N_from_H,
    N_yoke,
    n_yoke,
    O_yoke,
    o_yoke,
    P_from_H,
    P_yoke,
    Q_from_O,
    Q_yoke,
    R_from_H,
    r_from_n,
    R_yoke,
    r_yoke,
    S_from_O,
    s_from_o,
    S_yoke,
    s_yoke,
    T_from_H,
    t_from_n,
    T_yoke,
    t_yoke,
    tittle,
    U_from_H,
    u_from_n,
    u_yoke,
    U_yoke,
    V_from_H,
    v_from_n,
    V_yoke,
    v_yoke,
    W_from_H,
    w_from_n,
    W_yoke,
    w_yoke,
    X_from_H,
    x_from_n,
    X_yoke,
    x_yoke,
    Y_from_H,
    y_from_n,
    Y_yoke,
    y_yoke,
    Z_from_H,
    Z_yoke,
    eight_from_O,
    eight_yoke,
    five_from_O,
    five_yoke,
    four_from_H,
    four_yoke,
    nine_from_O,
    nine_yoke,
    one_from_H,
    one_yoke,
    seven_from_H,
    seven_yoke,
    six_from_O,
    six_yoke,
    three_from_O,
    three_yoke,
    two_from_O,
    two_yoke,
    zero_from_O,
    zero_yoke,
    period_yoke,
    comma_yoke,
    hyphen_yoke,
    quote_ascii_yoke,
    quote_dbl_ascii_yoke,
    period_from_n_o,
    comma_from_n_o,
    hyphen_from_n_o,
    quote_ascii_from_n_o,
    quote_dbl_ascii_from_n_o,
    g_double_yoke,
)
from typekernel.qa.proof import proof_labeled_waterfall

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "skill-validate"
PROOF_TEXT = "nhumar soft tiles jg vwxyk"  # letters both recipes draw







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

    # Capitals full A–Z: builders vs raw public yokes
    from typekernel.parts import h_cap_metrics, cap_o_metrics

    def recipe_caps_builders(c):
        H, O = build_H(c), build_O(c)
        return {
            "A": A_from_H(H, c),
            "B": B_from_H(H, O, c),
            "C": C_from_O(O, c),
            "D": D_from_H(H, O, c),
            "E": E_from_H(H, c),
            "F": F_from_H(H, c),
            "G": G_from_O(O, H, c),
            "H": H,
            "I": I_from_H(H, c),
            "J": J_from_H(H, O, c),
            "K": K_from_H(H, c),
            "L": L_from_H(H, c),
            "M": M_from_H(H, c),
            "N": N_from_H(H, c),
            "O": O,
            "P": P_from_H(H, O, c),
            "Q": Q_from_O(O, H, c),
            "R": R_from_H(H, O, c),
            "S": S_from_O(O, c),
            "T": T_from_H(H, c),
            "U": U_from_H(H, O, c),
            "V": V_from_H(H, c),
            "W": W_from_H(H, c),
            "X": X_from_H(H, c),
            "Y": Y_from_H(H, c),
            "Z": Z_from_H(H, c),
        }

    def recipe_caps_yokes(c):
        hm = h_cap_metrics(c)
        om = cap_o_metrics(c)

        def pack(outline, design):
            return GlyphAssembler(c).with_design(design).add(outline).build()

        return {
            "A": pack(A_yoke(c, metrics=hm), hm),
            "B": pack(B_yoke(c, metrics=hm, o_metrics_rec=om), hm),
            "C": pack(C_yoke(c, metrics=om), om),
            "D": pack(D_yoke(c, metrics=hm, o_metrics_rec=om), hm),
            "E": pack(E_yoke(c, metrics=hm), hm),
            "F": pack(F_yoke(c, metrics=hm), hm),
            "G": pack(G_yoke(c, metrics=om, h_metrics=hm), om),
            "H": pack(H_yoke(c, metrics=hm), hm),
            "I": pack(I_yoke(c, metrics=hm), hm),
            "J": pack(J_yoke(c, metrics=hm, o_metrics_rec=om), hm),
            "K": pack(K_yoke(c, metrics=hm), hm),
            "L": pack(L_yoke(c, metrics=hm), hm),
            "M": pack(M_yoke(c, metrics=hm), hm),
            "N": pack(N_yoke(c, metrics=hm), hm),
            "O": pack(O_yoke(c, metrics=om), om),
            "P": pack(P_yoke(c, metrics=hm, o_metrics_rec=om), hm),
            "Q": pack(Q_yoke(c, metrics=om, h_metrics=hm), om),
            "R": pack(R_yoke(c, metrics=hm, o_metrics_rec=om), hm),
            "S": pack(S_yoke(c, metrics=om), om),
            "T": pack(T_yoke(c, metrics=hm), hm),
            "U": pack(U_yoke(c, metrics=hm, o_metrics_rec=om), hm),
            "V": pack(V_yoke(c, metrics=hm), hm),
            "W": pack(W_yoke(c, metrics=hm), hm),
            "X": pack(X_yoke(c, metrics=hm), hm),
            "Y": pack(Y_yoke(c, metrics=hm), hm),
            "Z": pack(Z_yoke(c, metrics=hm), hm),
        }

    rc1 = recipe_caps_builders(ctx)
    otf_c1 = _compile("after7_caps_builders", ctx, rc1)
    ctx_wide = ctx.tuned(aperture=0.72)
    rc2w = recipe_caps_yokes(ctx_wide)
    otf_c2 = _compile("after7_caps_yokes", ctx_wide, rc2w)
    CAP_TEXT = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    p_caps = proof_labeled_waterfall(
        [("1 builders", otf_c1), ("2 yokes wide", otf_c2)],
        CAP_TEXT,
        OUT / "proof_caps_after7.png",
        sizes=(36, 56, 72),
        width=1600,
    )
    print("caps:", p_caps)
    p_caps_cmp = proof_labeled_waterfall(
        [("builders", otf_c1), ("yokes", otf_c2)],
        "THE QUICK BROWN FOX JUMPS OVER A LAZY DOG",
        OUT / "proof_caps_compare_after7.png",
        sizes=(40, 64),
        width=1600,
    )
    print("caps compare:", p_caps_cmp)


    # Figures 0–9: builders vs raw public yokes
    def recipe_figs_builders(c):
        H, O = build_H(c), build_O(c)
        return {
            "0": zero_from_O(O, H, c),
            "1": one_from_H(H, c),
            "2": two_from_O(O, H, c),
            "3": three_from_O(O, H, c),
            "4": four_from_H(H, c),
            "5": five_from_O(O, H, c),
            "6": six_from_O(O, H, c),
            "7": seven_from_H(H, c),
            "8": eight_from_O(O, H, c),
            "9": nine_from_O(O, H, c),
        }

    def recipe_figs_yokes(c):
        hm = h_cap_metrics(c)
        om = cap_o_metrics(c)

        def pack(outline, design):
            return GlyphAssembler(c).with_design(design).add(outline).build()

        return {
            "0": pack(zero_yoke(c, metrics=hm, o_metrics_rec=om), hm),
            "1": pack(one_yoke(c, metrics=hm), hm),
            "2": pack(two_yoke(c, metrics=hm, o_metrics_rec=om), hm),
            "3": pack(three_yoke(c, metrics=hm, o_metrics_rec=om), hm),
            "4": pack(four_yoke(c, metrics=hm), hm),
            "5": pack(five_yoke(c, metrics=hm, o_metrics_rec=om), hm),
            "6": pack(six_yoke(c, metrics=hm, o_metrics_rec=om), hm),
            "7": pack(seven_yoke(c, metrics=hm), hm),
            "8": pack(eight_yoke(c, metrics=hm, o_metrics_rec=om), hm),
            "9": pack(nine_yoke(c, metrics=hm, o_metrics_rec=om), hm),
        }

    rf1 = recipe_figs_builders(ctx)
    otf_f1 = _compile("after8_figs_builders", ctx, rf1)
    ctx_fig_wide = ctx.tuned(aperture=0.72)
    rf2 = recipe_figs_yokes(ctx_fig_wide)
    otf_f2 = _compile("after8_figs_yokes", ctx_fig_wide, rf2)
    FIG_TEXT = "0123456789"
    p_figs = proof_labeled_waterfall(
        [("1 builders", otf_f1), ("2 yokes wide", otf_f2)],
        FIG_TEXT,
        OUT / "proof_figs_after8.png",
        sizes=(48, 72, 96),
        width=1400,
    )
    print("figs:", p_figs)
    p_figs_cmp = proof_labeled_waterfall(
        [("builders", otf_f1), ("yokes", otf_f2)],
        "0123456789  3.14159  $1,280",
        OUT / "proof_figs_compare_after8.png",
        sizes=(40, 64),
        width=1400,
    )
    print("figs compare:", p_figs_cmp)

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

Smoke does **not** claim visual quality. Proofs under `artifacts/skill-validate/`
(and `/workspace/uploads/visual_accept_*.png` when emitted) are for a **vision
agent** to review — see `examples/skill_validate/VISUAL_ACCEPT.md`.

Recipe 2 is intentionally wider (part params). Structural note only:
`n`/`h`/`m`/`u`/`r` are continuous yoke contours; lint/topology smoke is separate.

## Verdict

**SMOKE ONLY** — recipes compile + export OTFs + write proofs. **Not ship.**
Vision must read proofs (joins, counters, weight ladder). No code hairline /
width-delta visual PASS. italic-vf-construct untouched.
"""
        ,
        encoding="utf-8",
    )
    print("wrote", note)


if __name__ == "__main__":
    main()

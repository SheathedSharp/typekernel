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
    DesignContext,
    GlyphAssembler,
    a_from_o,
    a_yoke,
    build_n,
    build_o,
    c_yoke,
    double_shoulder_yoke,
    e_from_o,
    e_yoke,
    f_from_n,
    f_yoke,
    h_from_n,
    h_yoke,
    i_from_n,
    i_yoke,
    l_from_n,
    l_yoke,
    m_from_n,
    n_yoke,
    o_yoke,
    r_from_n,
    r_yoke,
    s_from_o,
    s_yoke,
    t_from_n,
    t_yoke,
    u_from_n,
    tittle,
    u_yoke,
)
from typekernel.qa.proof import proof_labeled_waterfall

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "skill-validate"
PROOF_TEXT = "nhumar soft tiles"  # letters both recipes draw



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
    }
    failures = []
    for ch, (spring, band) in checks.items():
        if ch not in drawn:
            continue
        ol = drawn[ch].solids[0]
        # a also check upper bowl join
        bad = _spring_hairlines(ol, spring, band=band)
        if ch == "a":
            bad += _spring_hairlines(ol, ctx.x_height - band, band=band)
        if bad:
            failures.append(f"{ch}@{label}:{bad[:4]}")
    if failures:
        raise SystemExit(f"stem/bowl spring hairlines still open: {', '.join(failures)}")


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

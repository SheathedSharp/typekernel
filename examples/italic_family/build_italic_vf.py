"""Regular + ``ital`` axis VF (italic master via ``italic_design``).

``vf_italic_pair`` builds upright + italic sheets with matched construct slant (10°)
and VF segment compatibility (stem + bowl oblique pre-splits, wght×ital VF).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from typekernel.compile import build_font, build_variable_font
from typekernel.font import Font, Master
from typekernel.optics.space import space_font
from typekernel.parts import (
    Controls,
    DesignContext,
    auto_class_kern,
    auto_side_kern_classes,
    rhythm_from_control_glyphs,
)
from typekernel.parts.italic import vf_italic_pair
from typekernel.qa.proof import proof_labeled_waterfall, proof_weight_ladder
from typekernel.qa.sentence_gate import AGENT_SENTENCE

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "out"
FAMILY = "Typekernel Italic Var"
VF_LADDER_TEXT = (
    "nHamburgefons — wght ladder (ital=0). Compare italic masters in proof.png."
)


def master_font(
    controls: Controls,
    style: str,
    weight_class: int,
    kern_classes: tuple,
) -> Font:
    ctx = controls.context
    # Compose-time stock derivation after locked controls (not a DesignSequence design session).
    drawn = controls.build_all()
    rhythm = rhythm_from_control_glyphs(drawn["n"], drawn["o"])
    spaced = space_font(drawn, ctx, rhythm=rhythm)
    kerning = auto_class_kern(spaced, kern_classes, target=rhythm)
    font = Font.from_context(
        ctx, FAMILY, style, weight_class=weight_class, space_width=spaced["n"].advance * 0.45
    )
    font.add_chars(spaced)
    font.add_class_kern_table(kerning)
    return font


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=OUT_DIR,
        help="Output directory for VF binaries",
    )
    args = parser.parse_args()
    out_dir = args.out
    base = DesignContext.code_clear()
    reg, ital = vf_italic_pair(Controls.from_context(base))
    # Compose-time stock derivation after locked controls (not a DesignSequence design session).
    ref_drawn = reg.build_all()
    ref_rhythm = rhythm_from_control_glyphs(ref_drawn["n"], ref_drawn["o"])
    ref_spaced = space_font(ref_drawn, base, rhythm=ref_rhythm)
    kern_classes = auto_side_kern_classes(ref_spaced, base)
    bold, bold_ital = vf_italic_pair(
        Controls.from_context(base.tuned(stem=120.0)).with_stem_relief()
    )
    masters = [
        Master({"wght": 400, "ital": 0}, master_font(reg, "Regular", 400, kern_classes)),
        Master({"wght": 400, "ital": 1}, master_font(ital, "Italic", 400, kern_classes)),
        Master({"wght": 700, "ital": 0}, master_font(bold, "Bold", 700, kern_classes)),
        Master(
            {"wght": 700, "ital": 1},
            master_font(bold_ital, "Bold Italic", 700, kern_classes),
        ),
    ]
    result = build_variable_font(masters, out_dir, formats=("ttf",))
    for fmt, path in result.binaries.items():
        print(f"{fmt}: {path}")

    ttf = result.binaries["ttf"]
    vf_proof = proof_weight_ladder(ttf, VF_LADDER_TEXT, out_dir / "proof_vf.png")
    print(f"proof_vf: {vf_proof}")

    static_dir = out_dir / "static"
    otfs: list[tuple[str, Path]] = []
    for master in masters:
        label = master.style_name
        built = build_font(master.font, static_dir / label.lower().replace(" ", "_"), formats=("otf",))
        otf = built.binaries["otf"]
        otfs.append((label, otf))
        print(f"static {label} -> {otf}")
    proof = proof_labeled_waterfall(
        otfs,
        AGENT_SENTENCE,
        out_dir / "proof.png",
        sizes=(28, 48),
    )
    print(f"proof: {proof}")


if __name__ == "__main__":
    main()

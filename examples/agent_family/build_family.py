"""L2 static family: Regular + Light + Bold from separate control sheets.

Structure follows ``examples/first_font/build_font.py``. Fill the TODOs in
``design.py`` (name, proportions, italic, extended Latin). Do not pass the
brief sentence into the gate.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from design import (
    BRIEF_SENTENCE,
    FAMILY_NAME,
    baseline_controls,
    design_bold,
    design_controls,
    design_light,
)

from typekernel.compile import (
    FamilyBuildOptions,
    build_font,
    compose_font_from_controls,
    reference_kern_classes,
)
from typekernel.qa.design_review import design_review
from typekernel.qa.proof import proof_labeled_waterfall
from typekernel.qa.sentence_gate import AGENT_SENTENCE, check_sentence_gate

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"

# TODO: enable tnum / case / extended_latin only after those glyphs are proofed.
FAMILY_OPTIONS = FamilyBuildOptions(liga=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the agent_family static trio.")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    out = args.out

    regular = design_controls()
    light = design_light()
    bold = design_bold()

    review = design_review(regular, baseline=baseline_controls(), out_dir=out / "review")
    print(review.summary())
    if review.failures or review.l0_gaps:
        sys.exit(1)

    # Absolute ceilings only. Do not use the Regular preset as Bold's baseline.
    for label, sheet in (("Light", light), ("Bold", bold)):
        _report, failures = check_sentence_gate(sheet)
        if failures:
            print(f"{label} sentence gate:", *failures, sep="\n  ")
            sys.exit(1)
        print(f"{label} sentence gate ok")

    kern_classes = reference_kern_classes(regular)
    styles = (
        (regular, "Regular", 400),
        (light, "Light", 300),
        (bold, "Bold", 700),
    )
    otfs: list[tuple[str, Path]] = []
    for controls, style, weight in styles:
        font = compose_font_from_controls(
            controls,
            FAMILY_NAME,
            style,
            weight_class=weight,
            options=FAMILY_OPTIONS,
            kern_classes=kern_classes,
        )
        built = build_font(font, out, formats=("otf",))
        otf = built.binaries["otf"]
        otfs.append((style, otf))
        print(f"{style}: {otf}")

    proof = proof_labeled_waterfall(
        otfs,
        AGENT_SENTENCE,
        out / "proof.png",
        sizes=(28, 48),
    )
    proof_labeled_waterfall(
        otfs,
        BRIEF_SENTENCE,
        out / "proof_brief.png",
        sizes=(28, 48),
    )
    print(f"proof: {proof}")


if __name__ == "__main__":
    main()

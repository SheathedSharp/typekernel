"""Build Regular / Light / Bold bracketed serif static fonts (serif voices)."""

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

from typekernel.compile import FamilyBuildOptions, build_font, compose_font
from typekernel.qa.design_review import design_review
from typekernel.qa.proof import proof_labeled_waterfall
from typekernel.qa.sentence_gate import AGENT_SENTENCE, check_sentence_gate

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"

FAMILY_OPTIONS = FamilyBuildOptions(liga=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build bracketed serif Regular / Light / Bold.")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    regular = design_controls()
    light = design_light()
    bold = design_bold()

    review = design_review(regular, baseline=baseline_controls(), out_dir=out / "review")
    print(review.summary())
    if review.failures or review.l0_gaps or review.charset_failures:
        return 1

    for label, sheet in (("Regular", regular), ("Light", light), ("Bold", bold)):
        _report, failures = check_sentence_gate(sheet)
        if failures:
            print(f"{label} sentence gate:", *failures, sep="\n  ")
            return 1
        print(f"{label} sentence gate ok")

    styles = (
        (regular, "Regular", 400),
        (light, "Light", 300),
        (bold, "Bold", 700),
    )
    otfs: list[tuple[str, Path]] = []
    for controls, style_name, weight in styles:
        font = compose_font(
            controls.derive(),
            controls.context,
            FAMILY_NAME,
            style_name,
            weight_class=weight,
            options=FAMILY_OPTIONS,
        )
        built = build_font(font, out / style_name.lower(), formats=("otf",))
        otf = built.binaries["otf"]
        otfs.append((style_name, otf))
        print(f"built {style_name} -> {otf}")

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
    return 0


if __name__ == "__main__":
    sys.exit(main())

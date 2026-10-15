"""Build brief-1 reference trial: Regular + Bold OTFs and proofs (TK-502)."""

from __future__ import annotations

import argparse
from pathlib import Path

from design_warm_humanist import FAMILY_NAME, baseline_controls, controls, design_bold

from typekernel.compile import build_font, compose_font_from_controls, reference_kern_classes
from typekernel.qa.design_review import design_review
from typekernel.qa.proof import proof_labeled_waterfall
from typekernel.qa.sentence_gate import AGENT_SENTENCE, check_sentence_gate
from typekernel.qa.trial_protocol import FIXED_TRIAL_BRIEFS, snapshot_trial, write_trial_snapshot

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    regular = controls()
    bold = design_bold()
    brief = next(b for b in FIXED_TRIAL_BRIEFS if b.id == "brief-1")
    snap = snapshot_trial(
        regular,
        brief=brief,
        round=1,
        apis_used=("Style", "terminal_style", "tuned_glyph", "design_module"),
    )
    write_trial_snapshot(out / "snapshot.json", snap)
    if not snap.l3_voice_ok or not snap.metrics_ok or snap.weight_ladder_r8_failures:
        return 1

    review = design_review(regular, baseline=baseline_controls(), out_dir=out / "review")
    print(review.summary())
    if review.charset_failures:
        return 2

    # L3 voice intentionally diverges from preset; use absolute sentence ceilings only.
    for label, sheet in (("Regular", regular), ("Bold", bold)):
        _report, failures = check_sentence_gate(sheet)
        if failures:
            print(f"{label} sentence gate:", *failures, sep="\n  ")
            return 3
        print(f"{label} sentence gate ok")

    kern_classes = reference_kern_classes(regular)
    otfs: list[tuple[str, Path]] = []
    for sheet, style, weight in (
        (regular, "Regular", 400),
        (bold, "Bold", 700),
    ):
        font = compose_font_from_controls(
            sheet,
            FAMILY_NAME,
            style,
            weight_class=weight,
            kern_classes=kern_classes,
        )
        built = build_font(font, out, formats=("otf",))
        otf = built.binaries["otf"]
        otfs.append((style, otf))
        print(f"{style}: {otf}")

    proof = proof_labeled_waterfall(otfs, AGENT_SENTENCE, out / "proof.png", sizes=(28, 48))
    print(f"proof: {proof}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

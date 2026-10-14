"""Proof runner for an L0 trial. Art lives in :mod:`design`, not here."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from design import BRIEF_SENTENCE, FAMILY_NAME, FOCUS_GLYPHS, baseline_controls, design_controls

from typekernel.qa.agent_preview import build_glyph_preview
from typekernel.qa.design_review import design_review
from typekernel.qa.proof import proof_context
from typekernel.qa.sentence_gate import AGENT_SENTENCE

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="L0 proofs from examples/agent_studio/design.py (agent-authored)."
    )
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    controls = design_controls()
    review = design_review(
        controls,
        baseline=baseline_controls(),
        out_dir=args.out / "review",
    )
    print(review.summary())
    if review.charset_failures:
        print(f"charset issues (fix in library / M2): {len(review.charset_failures)}")

    paths = build_glyph_preview(
        controls,
        family=FAMILY_NAME,
        focus=FOCUS_GLYPHS,
        sentence=AGENT_SENTENCE,
        out_dir=args.out,
    )
    brief = proof_context(
        paths["otf"],
        BRIEF_SENTENCE,
        args.out / "sentence_brief.png",
        size=36,
        width=1600,
    )
    print(f"sentence_brief: {brief}")
    for name, path in paths.items():
        print(f"{name}: {path}")

    if review.failures or review.l0_gaps:
        sys.exit(1)


if __name__ == "__main__":
    main()

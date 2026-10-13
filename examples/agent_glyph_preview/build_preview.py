"""CLI wrapper for :func:`~typekernel.qa.agent_preview.build_glyph_preview`."""

from __future__ import annotations

import argparse
from pathlib import Path

from typekernel.qa.agent_preview import DEFAULT_FOCUS_GLYPHS, build_glyph_preview
from typekernel.qa.sentence_gate import AGENT_SENTENCE, check_sentence_gate
from typekernel.parts import Controls, DesignContext

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent glyph preview build")
    parser.add_argument("--chars", default=DEFAULT_FOCUS_GLYPHS.replace(" ", ""))
    parser.add_argument("--sentence", default=AGENT_SENTENCE)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    controls = Controls.from_context(DesignContext.code_clear())
    report, gate_fail = check_sentence_gate(controls, text=args.sentence)
    if gate_fail:
        print("sentence gate:", *gate_fail, sep="\n  ")
    else:
        print(
            f"sentence gate ok · optical ratio {report.optical_gap_ratio:.3f} · "
            f"G1(non-term) {report.g1_join_error_count - report.terminal_count}"
        )

    paths = build_glyph_preview(
        focus=args.chars,
        sentence=args.sentence,
        out_dir=args.out,
    )
    for name, path in paths.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()

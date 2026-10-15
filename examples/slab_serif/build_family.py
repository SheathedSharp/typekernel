"""Build Regular / Light / Bold slab serif static fonts (TK-306)."""

from __future__ import annotations

import sys
from pathlib import Path

from design import FAMILY_NAME, design_bold, design_controls, design_light

from typekernel.compile import FamilyBuildOptions, build_font, compose_font_from_controls
from typekernel.qa.family_gate import collect_family_gate_failures
from typekernel.qa.sentence_gate import AGENT_SENTENCE, check_sentence_gate

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"

FAMILY_OPTIONS = FamilyBuildOptions(liga=True)


def main() -> int:
    out = OUT
    out.mkdir(parents=True, exist_ok=True)
    sheets = (
        ("Regular", design_controls()),
        ("Light", design_light()),
        ("Bold", design_bold()),
    )
    for style_name, controls in sheets:
        failures = collect_family_gate_failures(controls)
        if failures:
            print(f"{style_name} family gate:", *failures, sep="\n  ")
            return 1
        _, gate_fail = check_sentence_gate(controls, text=AGENT_SENTENCE)
        if gate_fail:
            print(f"{style_name} sentence gate (warning):", *gate_fail, sep="\n  ")
        font = compose_font_from_controls(
            controls,
            FAMILY_NAME,
            style_name,
            options=FAMILY_OPTIONS,
        )
        build_font(font, out / style_name.lower())
        print(f"built {style_name} -> {out / style_name.lower()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

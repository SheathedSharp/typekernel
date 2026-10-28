#!/usr/bin/env python3
"""Scaffold latin-sans → build OTF → write a control proof PNG.

Demonstrates the current path: Project / @glyph / System — no ``parts``.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from typekernel.cli.build import build_project
from typekernel.cli.new import create_project
from typekernel.qa.proof import proof_context


def main() -> int:
    out = Path(__file__).resolve().parent / "out"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()

    with tempfile.TemporaryDirectory(prefix="tk-quickstart-") as tmp:
        root = create_project("quick", parent=tmp, starter="latin-sans")
        font, result = build_project(root, out_dir=out / "build", formats=("otf",))
        otf = result.binaries["otf"]
        proof = proof_context(
            otf,
            "nnonoo HHOHOO hamburgefonstiv",
            out / "control.png",
            size=40,
        )
        print(f"glyphs: {len(font)}")
        print(f"otf: {otf}")
        print(f"proof: {proof}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

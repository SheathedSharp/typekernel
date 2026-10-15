"""Run M5 *program* exit checks (DEVELOPMENT_PLAN §8 hooks + pending gate tests).

This is **not** TK-502 final agent validation and does not write ``approvals/*.json``.

Example::

    PYTHONPATH=src python examples/run_m5_program_exit.py
    PYTHONPATH=src python examples/run_m5_program_exit.py --gate slab
    PYTHONPATH=src python examples/run_m5_program_exit.py --list
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from typekernel.qa.gates import load_approval

ROOT = Path(__file__).resolve().parents[1]
SECTION8 = "tests/docs/test_development_plan_section8.py"

_GATE_FILES = {
    "slab": "approvals/serif-slab-voice.json",
    "bracketed": "approvals/serif-bracketed-voice.json",
    "italic": "approvals/italic-vf-construct.json",
}


def _evidence_paths(gate: str) -> tuple[str, ...]:
    if gate == "section8":
        return (SECTION8,)
    if gate == "all":
        paths: list[str] = [SECTION8]
        for rel in _GATE_FILES.values():
            paths.extend(load_approval(ROOT / rel)["test_evidence"])
        return tuple(dict.fromkeys(paths))
    rel = _GATE_FILES[gate]
    return (SECTION8, *load_approval(ROOT / rel)["test_evidence"])


def _pytest_argv(paths: tuple[str, ...]) -> list[str]:
    return [sys.executable, "-m", "pytest", "-q", *paths]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gate",
        choices=("all", "section8", "slab", "bracketed", "italic"),
        default="all",
        help="which program checks to run (always includes §8 when not section8-only)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="print pytest paths and exit without running",
    )
    args = parser.parse_args(argv)
    paths = _evidence_paths(args.gate)
    if args.list:
        for p in paths:
            print(p)
        return 0
    proc = subprocess.run(_pytest_argv(paths), cwd=ROOT, check=False)
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())

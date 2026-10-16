"""Run program exit checks (DEVELOPMENT_PLAN §8 hooks + pending gate tests).

This is **not** final agent validation and does not write ``approvals/*.json``.

Example::

    PYTHONPATH=src python examples/run_program_exit.py
    PYTHONPATH=src python examples/run_program_exit.py --gate slab
    PYTHONPATH=src python examples/run_program_exit.py --list
    PYTHONPATH=src python examples/run_program_exit.py --with-linters
    PYTHONPATH=src python examples/run_program_exit.py --full-suite --with-linters
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from typekernel.qa.gates import load_approval

ROOT = Path(__file__).resolve().parents[1]
SECTION8 = "tests/docs/test_development_plan_section8.py"
_TRIAL_SMOKE = (
    "tests/examples/test_agent_trial.py",
    "tests/examples/test_agent_trial_reference.py",
    "tests/examples/test_weight_ladder_sheet.py",
    "tests/examples/test_contact_sheet.py",
    "tests/examples/test_diff_overlay.py",
    "tests/examples/test_regenerate_outline_hashes.py",
    "tests/examples/test_human_review_bundle.py::test_human_review_bundle_source_documents_pending_gates",
    "tests/examples/test_human_review_bundle.py::test_human_review_bundle_appendix_b_only",
    "tests/parts/test_known_defects.py::test_b13_three_no_flat_top_shelf",
    "tests/parts/test_known_defects.py::test_b14_g_spur_cubic_join",
    "tests/parts/test_known_defects.py::test_b15_s_spine_ink_is_continuous_band",
    "tests/parts/test_control_gs.py::test_s_opening_reach_relief_frozen",
    "tests/parts/test_knob_coverage.py",
    "tests/parts/test_extended_latin_policy.py",
    "tests/parts/test_glyph_specs.py",
    "tests/parts/test_stroke_program_acceptance.py",
    "tests/examples/test_zayju_script.py::test_zayju_script_charset_builds_and_lints_clean",
    "tests/parts/test_stress.py",
    "tests/parts/test_figures.py::test_all_lining_figures_build_under_stress",
    "tests/qa/test_gate_thresholds_locked.py",
    "tests/qa/test_counter.py::test_descender_micro_sliver_below_min_run_gap_ignored",
    "tests/qa/test_sheet.py::test_contact_sheet_full_charset_width_at_most_1600",
    "tests/qa/test_sheet.py::test_diff_overlay_writes",
    "tests/qa/test_trial_protocol.py",
    "tests/qa/test_multi_voice_exit.py",
)

_GATE_FILES = {
    "slab": "approvals/serif-slab-voice.json",
    "bracketed": "approvals/serif-bracketed-voice.json",
    "italic": "approvals/italic-vf-construct.json",
}


def _evidence_paths(gate: str) -> tuple[str, ...]:
    if gate == "section8":
        return (SECTION8,)
    if gate == "all":
        paths: list[str] = [SECTION8, *_TRIAL_SMOKE]
        for rel in _GATE_FILES.values():
            paths.extend(load_approval(ROOT / rel)["test_evidence"])
        return tuple(dict.fromkeys(paths))
    rel = _GATE_FILES[gate]
    merged = (SECTION8, *load_approval(ROOT / rel)["test_evidence"])
    return tuple(dict.fromkeys(merged))


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
    parser.add_argument(
        "--with-linters",
        action="store_true",
        help="after pytest, run ruff check src tests and mypy -p typekernel (DEVELOPMENT_PLAN §8.1)",
    )
    parser.add_argument(
        "--full-suite",
        action="store_true",
        help="run entire test suite (pytest -q) instead of §8 + pending gate subset",
    )
    args = parser.parse_args(argv)
    if args.full_suite and args.gate != "all":
        parser.error("--full-suite cannot be combined with --gate other than all")
    paths = _evidence_paths(args.gate)
    if args.list:
        if args.full_suite:
            print("pytest -q  # entire suite")
        else:
            for p in paths:
                print(p)
        return 0
    if args.full_suite:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=ROOT,
            check=False,
        )
    else:
        proc = subprocess.run(_pytest_argv(paths), cwd=ROOT, check=False)
    if proc.returncode != 0:
        return int(proc.returncode)
    if not args.with_linters:
        return 0
    ruff = subprocess.run(["ruff", "check", "src", "tests"], cwd=ROOT, check=False)
    if ruff.returncode != 0:
        return int(ruff.returncode)
    mypy = subprocess.run(
        [sys.executable, "-m", "mypy", "-p", "typekernel"],
        cwd=ROOT,
        check=False,
    )
    return int(mypy.returncode)


if __name__ == "__main__":
    raise SystemExit(main())

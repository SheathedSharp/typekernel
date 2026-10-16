"""Generate local PNG/TTF bundles for TK-306 / TK-402 / TK-206 B-15 review.

Does **not** write ``approvals/*.json`` — only artifacts under ``--out`` (gitignored).

Example::

    PYTHONPATH=src python examples/human_review_bundle.py \\
        --out artifacts/human-review

    PYTHONPATH=src python examples/human_review_bundle.py \\
        --only tk206 --out artifacts/human-review
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

_CHECKLIST = """# Human review checklist (do not commit this folder)

## Automated gates (run from repo root)

```bash
PYTHONPATH=src python examples/run_m5_program_exit.py --gate all
pytest -q tests/docs/test_development_plan_section8.py
pytest -q tests/examples/test_agent_trial_reference.py
pytest -q tests/qa/test_m3_exit.py
pytest -q tests/examples/test_human_review_bundle.py
pytest -q tests/examples/test_weight_ladder_sheet.py
pytest -q tests/parts/test_known_defects.py::test_b13_three_no_flat_top_shelf
pytest -q tests/parts/test_known_defects.py::test_b14_g_spur_cubic_join
pytest -q tests/parts/test_known_defects.py::test_b15_s_spine_ink_is_continuous_band
pytest -q tests/parts/test_control_gs.py::test_s_opening_reach_relief_frozen
pytest -q tests/examples/test_slab_serif.py tests/examples/test_bracketed_serif.py
pytest -q tests/parts/test_serifs.py::test_serif_voice_meets_tk306_program_acceptance
pytest -q tests/qa/test_originality.py tests/qa/test_sentence_gate.py
pytest -q tests/examples/test_italic_family.py
pytest -q tests/parts/test_italic_program_acceptance.py
```

## TK-306 serif voices — open these PNGs

| Voice | Static proofs | VF proof | Weight ladder |
| --- | --- | --- | --- |
| Slab | `{out}/slab_serif/proof.png`, `proof_brief.png` | `{out}/slab_serif_vf/proof_vf.png` | `{out}/weight_ladder_slab_serif.png` |
| Bracketed | `{out}/bracketed_serif/proof.png`, `proof_brief.png` | `{out}/bracketed_serif_vf/proof_vf.png` | `{out}/weight_ladder_bracketed_serif.png` |

Judge: serif feet/caps, counters at bold, brief sentence legibility, VF interpolation (no kinks).

Other presets (TK-207): ``PYTHONPATH=src python examples/weight_ladder_sheet.py --preset humanist_sans --out artifacts/specimens/weight_ladder.png``

## TK-206 appendix B-13–B-15 (no approvals JSON)

| Defect | Artifact | Path |
| --- | --- | --- |
| B-13 `3` top | Humanist `3G` contact | `{out}/tk206_three_g_humanist.png` |
| B-14 `G` spur | (same sheet) | |
| B-15 `s` opening | Humanist `sS` contact | `{out}/tk206_s_opening_humanist.png` |

Judge: `3` cap without a flat Ʒ shelf; `G` spur meets bowl on a smooth cubic; `s`/`S` opening natural with a
continuous spine band at bold weights. Program hooks: ``test_b13_three_no_flat_top_shelf``,
``test_b14_g_spur_cubic_join``, ``test_b15_s_spine_ink_is_continuous_band``, ``test_s_opening_reach_relief_frozen``.
Changing ``S_OPENING_REACH_RELIEF`` or outline builders requires ``regenerate_outline_hashes.py --write`` and new specimens.

Regenerate PNGs::

    PYTHONPATH=src python examples/contact_sheet.py --preset humanist_sans --chars 3G \\
        --out artifacts/specimens/tk206_three_g_humanist.png
    PYTHONPATH=src python examples/contact_sheet.py --preset humanist_sans --chars sS \\
        --out artifacts/specimens/tk206_s_opening_humanist.png

After **you** accept visually, record decisions (agent must not set ``approved: true`` without you):

```python
from typekernel.qa.gates import write_approval

write_approval(
    "approvals/serif-slab-voice.json",
    gate="serif-slab-voice",
    approved=True,  # only after your review
    approver="YOUR_NAME",
    date="YYYY-MM-DD",
    notes="Reviewed slab_serif proofs under artifacts/human-review/…",
    scope="DesignContext.slab_serif + examples/slab_serif",
    test_evidence=[
        "tests/examples/test_slab_serif.py",
        "tests/examples/test_human_review_bundle.py",
        "tests/parts/test_serifs.py",
        "tests/qa/test_m3_exit.py",
        "tests/qa/test_originality.py",
        "tests/qa/test_sentence_gate.py",
        "tests/docs/test_development_plan_section8.py",
    ],
)

write_approval(
    "approvals/serif-bracketed-voice.json",
    gate="serif-bracketed-voice",
    approved=True,  # only after your review
    approver="YOUR_NAME",
    date="YYYY-MM-DD",
    notes="Reviewed bracketed_serif proofs under artifacts/human-review/…",
    scope="DesignContext.bracketed_serif + examples/bracketed_serif",
    test_evidence=[
        "tests/examples/test_bracketed_serif.py",
        "tests/examples/test_human_review_bundle.py",
        "tests/parts/test_serifs.py",
        "tests/qa/test_m3_exit.py",
        "tests/qa/test_originality.py",
        "tests/qa/test_sentence_gate.py",
        "tests/docs/test_development_plan_section8.py",
    ],
)
```

## TK-402 true italic — open

| Artifact | Path |
| --- | --- |
| wght×ital VF | `{out}/italic_family/*.ttf` |
| Sentence proof (4 masters) | `{out}/italic_family/proof.png` |
| VF weight ladder | `{out}/italic_family/proof_vf.png` |

Judge: construct slant vs mechanical oblique, branching ``n``/``h``, bold italic counters.

```python
write_approval(
    "approvals/italic-vf-construct.json",
    gate="italic-vf-construct",
    approved=True,  # only after your review
    approver="YOUR_NAME",
    date="YYYY-MM-DD",
    notes="Reviewed italic_family proof.png / proof_vf.png under artifacts/human-review/…",
    scope="examples/italic_family build_italic_vf wght×ital",
    test_evidence=[
        "tests/examples/test_human_review_bundle.py",
        "tests/examples/test_italic_family.py",
        "tests/parts/test_italic_program_acceptance.py",
        "tests/parts/test_italic_controls.py",
        "tests/parts/test_italic_topology.py",
        "tests/parts/test_oblique_compat.py",
        "tests/docs/test_development_plan_section8.py",
    ],
)
```

**Never** change ``AGENT_SENTENCE`` or L3 thresholds to pass gate.
"""


def _run(cmd: list[str], *, cwd: Path) -> None:
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    proc = subprocess.run(cmd, cwd=cwd, env=env, check=False)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def _serif_bundle(out: Path) -> None:
    slab = ROOT / "examples" / "slab_serif"
    bracket = ROOT / "examples" / "bracketed_serif"
    _run(
        [sys.executable, "build_family.py", "--out", str(out / "slab_serif")],
        cwd=slab,
    )
    _run(
        [sys.executable, "build_vf.py", "--out", str(out / "slab_serif_vf")],
        cwd=slab,
    )
    _run(
        [sys.executable, "build_family.py", "--out", str(out / "bracketed_serif")],
        cwd=bracket,
    )
    _run(
        [sys.executable, "build_vf.py", "--out", str(out / "bracketed_serif_vf")],
        cwd=bracket,
    )
    from typekernel.parts import DesignContext
    from typekernel.qa.sheet import weight_ladder_sheet

    weight_ladder_sheet(
        DesignContext.slab_serif(),
        out / "weight_ladder_slab_serif.png",
    )
    weight_ladder_sheet(
        DesignContext.bracketed_serif(),
        out / "weight_ladder_bracketed_serif.png",
    )


def _italic_bundle(out: Path) -> None:
    italic = ROOT / "examples" / "italic_family"
    _run(
        [sys.executable, "build_italic_vf.py", "--out", str(out / "italic_family")],
        cwd=italic,
    )


def _tk206_review_bundle(out: Path) -> None:
    from typekernel.parts import Controls, DesignContext
    from typekernel.qa.sheet import contact_sheet

    controls = Controls.from_context(DesignContext.humanist_sans())
    contact_sheet(controls, out / "tk206_three_g_humanist.png", chars="3G")
    contact_sheet(controls, out / "tk206_s_opening_humanist.png", chars="sS")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "artifacts" / "human-review",
        help="output root (should stay gitignored)",
    )
    parser.add_argument(
        "--only",
        choices=("all", "serif", "italic", "tk206"),
        default="all",
        help="which bundle to render",
    )
    args = parser.parse_args(argv)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)

    if args.only in ("all", "serif"):
        _serif_bundle(out)
    if args.only in ("all", "italic"):
        _italic_bundle(out)
    if args.only in ("all", "tk206"):
        _tk206_review_bundle(out)

    checklist = out / "REVIEW_CHECKLIST.md"
    checklist.write_text(_CHECKLIST.format(out=out), encoding="utf-8")
    print(f"checklist: {checklist}")
    print("Open PNGs/TTF listed there; write approvals/*.json yourself after review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Write ``snapshot_trial`` JSON for a Python design module (TK-502)."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

from typekernel.parts import Controls
from typekernel.qa.trial_protocol import (
    FIXED_TRIAL_BRIEFS,
    TrialBrief,
    snapshot_trial,
    write_trial_snapshot,
)

APIS_USED = ("Style", "terminal_style", "tuned_glyph", "design_module")


def _load_controls(path: Path) -> Controls:
    spec = importlib.util.spec_from_file_location("trial_design", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "controls"):
        raise SystemExit(f"{path} must define controls() -> Controls")
    ctrl = mod.controls()
    if not isinstance(ctrl, Controls):
        raise SystemExit("controls() must return Controls")
    return ctrl


def _brief(brief_id: str) -> TrialBrief:
    for b in FIXED_TRIAL_BRIEFS:
        if b.id == brief_id:
            return b
    raise SystemExit(f"unknown brief {brief_id!r}; use one of {[b.id for b in FIXED_TRIAL_BRIEFS]}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--brief", required=True, help="brief-1, brief-2, or brief-3")
    p.add_argument(
        "--design",
        type=Path,
        default=Path(__file__).with_name("design_warm_humanist.py"),
        help="Python file exporting controls()",
    )
    p.add_argument("--out", type=Path, required=True, help="output directory")
    p.add_argument("--round", type=int, default=1, dest="round_no")
    args = p.parse_args(argv)

    brief = _brief(args.brief)
    controls = _load_controls(args.design.resolve())
    snap = snapshot_trial(
        controls,
        brief=brief,
        round=args.round_no,
        apis_used=APIS_USED,
    )
    args.out.mkdir(parents=True, exist_ok=True)
    path = write_trial_snapshot(args.out / "snapshot.json", snap)
    print(path)
    if not snap.metrics_ok:
        return 2
    if not snap.family_gate_ok:
        return 3
    if snap.weight_ladder_r8_failures:
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

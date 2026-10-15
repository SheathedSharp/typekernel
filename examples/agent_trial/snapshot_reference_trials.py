"""Write snapshot.json for all three TK-502 reference design modules."""

from __future__ import annotations

import argparse
from pathlib import Path

from snapshot_design import _brief, _load_controls

from typekernel.qa.trial_protocol import write_trial_snapshot

_REFERENCE: tuple[tuple[str, str, Path], ...] = (
    ("brief-1", "brief-1", Path(__file__).with_name("design_warm_humanist.py")),
    ("brief-2", "brief-2", Path(__file__).with_name("design_editorial_geometric.py")),
    ("brief-2-slab", "brief-2", Path(__file__).with_name("design_editorial_slab.py")),
    ("brief-3", "brief-3", Path(__file__).with_name("design_coding_clear.py")),
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, required=True, help="base output directory")
    args = p.parse_args(argv)
    from typekernel.qa.trial_protocol import snapshot_trial

    apis = ("Style", "terminal_style", "tuned_glyph", "design_module")
    worst = 0
    for folder_id, brief_id, design_path in _REFERENCE:
        brief = _brief(brief_id)
        controls = _load_controls(design_path.resolve())
        snap = snapshot_trial(controls, brief=brief, round=1, apis_used=apis)
        sub = args.out / folder_id
        sub.mkdir(parents=True, exist_ok=True)
        write_trial_snapshot(sub / "snapshot.json", snap)
        if not snap.metrics_ok:
            worst = max(worst, 2)
        if not snap.family_gate_ok:
            worst = max(worst, 3)
        if snap.weight_ladder_r8_failures:
            worst = max(worst, 4)
        if not snap.l3_voice_ok:
            worst = max(worst, 5)
    return worst


if __name__ == "__main__":
    raise SystemExit(main())

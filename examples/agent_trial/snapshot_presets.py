"""Write DEVELOPMENT_PLAN §6 preset baseline snapshots (no agent edits)."""

from __future__ import annotations

import argparse
from pathlib import Path

from typekernel.parts import Controls, DesignContext
from typekernel.qa.trial_protocol import (
    FIXED_TRIAL_BRIEFS,
    snapshot_trial,
    write_trial_snapshot,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("artifacts/trials/preset-baseline"),
        help="Directory for per-brief snapshot.json files",
    )
    args = parser.parse_args()
    factories = {
        "humanist_sans": DesignContext.humanist_sans,
        "geometric_sans": DesignContext.geometric_sans,
        "code_clear": DesignContext.code_clear,
    }
    for brief in FIXED_TRIAL_BRIEFS:
        factory = factories[brief.preset]
        controls = Controls.from_context(factory())
        snap = snapshot_trial(controls, brief=brief, round=0, apis_used=("preset_only",))
        path = write_trial_snapshot(args.out / brief.id / "snapshot.json", snap)
        print(f"{brief.id}: gate_ok={snap.family_gate_ok} voice_distance={snap.voice_distance:.3f} -> {path}")


if __name__ == "__main__":
    main()

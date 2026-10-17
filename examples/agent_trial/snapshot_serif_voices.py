"""L3 serif voice baselines for agent trial (preset-only, no agent edits)."""

from __future__ import annotations

import argparse
from pathlib import Path

from typekernel.parts import Controls, DesignContext
from typekernel.qa.trial_protocol import (
    FIXED_TRIAL_BRIEFS,
    snapshot_trial,
    write_trial_snapshot,
)

_SERIF_VOICES = (
    ("slab_serif", DesignContext.slab_serif),
    ("bracketed_serif", DesignContext.bracketed_serif),
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("artifacts/trials/serif-voices"),
        help="Directory for per-voice snapshot.json",
    )
    args = parser.parse_args()
    brief = FIXED_TRIAL_BRIEFS[1]
    for voice_id, factory in _SERIF_VOICES:
        controls = Controls.from_context(factory())
        snap = snapshot_trial(
            controls,
            brief=brief,
            round=0,
            apis_used=("preset_only", voice_id),
        )
        path = write_trial_snapshot(args.out / voice_id / "snapshot.json", snap)
        print(
            f"{voice_id}: gate_ok={snap.family_gate_ok} "
            f"l3_ok={snap.l3_voice_ok} voice_distance={snap.voice_distance:.3f} -> {path}"
        )


if __name__ == "__main__":
    main()

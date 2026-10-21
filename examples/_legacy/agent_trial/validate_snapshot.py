"""Validate written ``snapshot.json`` files (agent trial final-trial audit)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from typekernel.qa.trial_protocol import (
    read_trial_snapshot_json,
    trial_snapshot_json_exit_code,
    validate_trial_snapshot_record,
)


def _collect_snapshot_paths(items: tuple[Path, ...], *, recursive: bool) -> list[Path]:
    paths: list[Path] = []
    for item in items:
        if item.is_dir():
            if recursive:
                paths.extend(sorted(item.rglob("snapshot.json")))
            else:
                paths.append(item / "snapshot.json")
        else:
            paths.append(item)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "snapshots",
        nargs="+",
        type=Path,
        help="paths to snapshot.json (or directories containing snapshot.json)",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="when a path is a directory, validate every snapshot.json beneath it",
    )
    parser.add_argument(
        "--require-human-scores",
        action="store_true",
        help="after program pass, require complete human_review_scores (exit 8 if missing)",
    )
    parser.add_argument(
        "--program-snapshot-only",
        action="store_true",
        help="reject JSON that already contains human_review_scores (exit 5)",
    )
    args = parser.parse_args(argv)
    if args.require_human_scores and args.program_snapshot_only:
        parser.error("--require-human-scores and --program-snapshot-only are mutually exclusive")
    paths = _collect_snapshot_paths(tuple(args.snapshots), recursive=args.recursive)
    worst = 0
    for path in paths:
        if not path.is_file():
            print(f"missing: {path}", file=sys.stderr)
            worst = max(worst, 2)
            continue
        data = read_trial_snapshot_json(path)
        problems = validate_trial_snapshot_record(
            data,
            program_snapshot_only=args.program_snapshot_only,
        )
        for msg in problems:
            print(f"{path}: validate: {msg}", flush=True)
        code = trial_snapshot_json_exit_code(
            data,
            problems,
            require_human_scores=args.require_human_scores,
        )
        if code != 0:
            print(f"{path}: exit {code}", flush=True)
        worst = max(worst, code)
    return worst


if __name__ == "__main__":
    raise SystemExit(main())

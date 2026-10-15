"""Validate written ``snapshot.json`` files (TK-502 final-trial audit)."""

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
    args = parser.parse_args(argv)
    paths = _collect_snapshot_paths(tuple(args.snapshots), recursive=args.recursive)
    worst = 0
    for path in paths:
        if not path.is_file():
            print(f"missing: {path}", file=sys.stderr)
            worst = max(worst, 2)
            continue
        data = read_trial_snapshot_json(path)
        problems = validate_trial_snapshot_record(data)
        for msg in problems:
            print(f"{path}: validate: {msg}", flush=True)
        code = trial_snapshot_json_exit_code(data, problems)
        if code != 0:
            print(f"{path}: exit {code}", flush=True)
        worst = max(worst, code)
    return worst


if __name__ == "__main__":
    raise SystemExit(main())

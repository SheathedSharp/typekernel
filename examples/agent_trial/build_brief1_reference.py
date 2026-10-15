"""Build brief-1 reference trial (delegates to :mod:`build_reference_family`)."""

from __future__ import annotations

import argparse
from pathlib import Path

from build_reference_family import build

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    return build("brief-1", args.out)


if __name__ == "__main__":
    raise SystemExit(main())

"""Write a TK-207 weight-ladder PNG for human review (local artifacts only)."""

from __future__ import annotations

import argparse
from pathlib import Path

from _design_presets import PRESET_FACTORIES as _PRESETS

from typekernel.qa.sheet import weight_ladder_sheet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preset",
        choices=sorted(_PRESETS),
        default="humanist_sans",
        help="built-in DesignContext preset",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("artifacts/specimens/weight_ladder.png"),
        help="output PNG path (parent dirs created)",
    )
    args = parser.parse_args(argv)
    factory = _PRESETS[args.preset]
    path = weight_ladder_sheet(factory(), args.out)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

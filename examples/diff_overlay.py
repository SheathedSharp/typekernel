"""Write a contact sheet trial-vs-baseline diff overlay PNG (local artifacts only)."""

from __future__ import annotations

import argparse
from pathlib import Path

from _design_presets import PRESET_FACTORIES as _PRESETS

from typekernel.parts import FormSources
from typekernel.qa.sheet import diff_overlay, review_index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--trial-preset",
        choices=sorted(_PRESETS),
        required=True,
        help="trial voice (red)",
    )
    parser.add_argument(
        "--baseline-preset",
        choices=sorted(_PRESETS),
        required=True,
        help="comparison voice (blue)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("artifacts/specimens/diff_overlay.png"),
        help="output PNG path (parent dirs created)",
    )
    parser.add_argument(
        "--chars",
        default="mutj&#!$",
        help="glyphs to compare side by side",
    )
    parser.add_argument(
        "--index",
        action="store_true",
        help="also write index.json beside the PNG",
    )
    args = parser.parse_args(argv)
    trial = FormSources.from_context(_PRESETS[args.trial_preset]())
    baseline = FormSources.from_context(_PRESETS[args.baseline_preset]())
    path = diff_overlay(trial, baseline, args.out, chars=args.chars)
    print(path)
    if args.index:
        index = review_index(path.parent, {"diff_overlay": path})
        print(index)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

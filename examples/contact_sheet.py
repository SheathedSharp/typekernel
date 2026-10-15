"""Write a TK-104 full-charset contact sheet PNG (local artifacts only)."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path

from typekernel.parts import Controls, DesignContext
from typekernel.qa.sheet import contact_sheet, review_index

_PRESETS: dict[str, Callable[[], DesignContext]] = {
    "humanist_sans": DesignContext.humanist_sans,
    "code_clear": DesignContext.code_clear,
    "geometric_sans": DesignContext.geometric_sans,
    "mono": DesignContext.mono,
    "display": DesignContext.display,
    "paper_ink": DesignContext.paper_ink,
    "open_print": DesignContext.open_print,
    "slab_serif": DesignContext.slab_serif,
    "bracketed_serif": DesignContext.bracketed_serif,
}


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
        default=Path("artifacts/specimens/contact.png"),
        help="output PNG path (parent dirs created)",
    )
    parser.add_argument(
        "--chars",
        default=None,
        help="subset of supported charset (default: full supported)",
    )
    parser.add_argument(
        "--no-zones",
        action="store_true",
        help="omit baseline/x-height guide lines",
    )
    parser.add_argument(
        "--index",
        action="store_true",
        help="also write index.json beside the PNG",
    )
    args = parser.parse_args(argv)
    controls = Controls.from_context(_PRESETS[args.preset]())
    path = contact_sheet(
        controls,
        args.out,
        chars=args.chars,
        zones=not args.no_zones,
    )
    print(path)
    if args.index:
        index = review_index(path.parent, {"contact": path})
        print(index)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""``python -m typekernel.cli`` / ``tk`` entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _cmd_new(args: argparse.Namespace) -> int:
    from typekernel.cli.new import create_project

    root = create_project(args.name, parent=args.parent, starter=args.starter)
    print(f"created {root}")
    return 0


def _cmd_build(args: argparse.Namespace) -> int:
    from typekernel.cli.build import build_project

    root = Path(args.path).resolve()
    font, result = build_project(root, out_dir=args.out, formats=tuple(args.format))
    print(f"glyphs: {len(font)}")
    print(f"ufo: {result.ufo}")
    for fmt, path in result.binaries.items():
        print(f"{fmt}: {path}")
    return 0


def _cmd_proof(args: argparse.Namespace) -> int:
    from typekernel.cli.proof_cmd import PROOF_SETS, proof_project

    paths = proof_project(
        args.path,
        args.set,
        out_dir=args.out,
        build_dir=args.build_dir,
    )
    for p in paths:
        print(p)
    if args.set not in PROOF_SETS:
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tk",
        description="typekernel project tools (ARCHITECTURE.md M2)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new", help="scaffold an empty project")
    p_new.add_argument("name", help="project directory name")
    p_new.add_argument(
        "--parent",
        default=".",
        help="parent directory for the new project (default: .)",
    )
    p_new.add_argument(
        "--starter",
        default=None,
        help="starter template: omit/empty, or latin-sans (control glyphs n o H O)",
    )
    p_new.set_defaults(func=_cmd_new)

    p_build = sub.add_parser("build", help="compile project glyphs to UFO/OTF/TTF")
    p_build.add_argument(
        "path",
        nargs="?",
        default=".",
        help="project root containing font.py (default: .)",
    )
    p_build.add_argument(
        "--out",
        default=None,
        help="output directory (default: <project>/build)",
    )
    p_build.add_argument(
        "--format",
        action="append",
        choices=("otf", "ttf", "woff2"),
        default=None,
        help="output format (repeatable; default: otf)",
    )
    p_build.set_defaults(func=_cmd_build)

    p_proof = sub.add_parser("proof", help="render proof PNGs from the built font")
    p_proof.add_argument(
        "set",
        help="proof set: control | spacing | kern | charset | all",
    )
    p_proof.add_argument(
        "path",
        nargs="?",
        default=".",
        help="project root (default: .)",
    )
    p_proof.add_argument("--out", default=None, help="PNG output directory")
    p_proof.add_argument(
        "--build-dir",
        default=None,
        help="directory with OTF/TTF (default: <project>/build)",
    )
    p_proof.set_defaults(func=_cmd_proof)

    args = parser.parse_args(argv)
    if args.command == "build" and not args.format:
        args.format = ["otf"]
    try:
        return int(args.func(args))
    except (FileNotFoundError, FileExistsError, ValueError, AttributeError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except ImportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

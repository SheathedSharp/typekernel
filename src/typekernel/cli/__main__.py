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
    from typekernel.cli.build import build_project, build_variable_project

    root = Path(args.path).resolve()
    resolve = bool(getattr(args, "resolve_overlaps", False))
    if getattr(args, "variable", False):
        if resolve:
            print(
                "error: --resolve-overlaps is static-export only; "
                "variable fonts must keep overlapping masters "
                "(ARCHITECTURE overlap construction)",
                file=sys.stderr,
            )
            return 2
        masters, vf = build_variable_project(
            root, out_dir=args.out, formats=tuple(args.format) or ("ttf",)
        )
        print(f"masters: {', '.join(m.style_name for m in masters)}")
        print(f"designspace: {vf.designspace}")
        for fmt, path in vf.binaries.items():
            print(f"{fmt}: {path}")
        for path in vf.masters:
            print(f"ufo: {path}")
        if vf.warnings:
            print(f"warnings: {len(vf.warnings)}")
        return 0
    font, built = build_project(
        root,
        out_dir=args.out,
        formats=tuple(args.format),
        resolve_overlaps=resolve,
    )
    print(f"glyphs: {len(font)}")
    print(f"ufo: {built.ufo}")
    for fmt, path in built.binaries.items():
        print(f"{fmt}: {path}")
    if resolve:
        print("resolve-overlaps: on (static packaging; not a design seal)")
    return 0


def _cmd_proof(args: argparse.Namespace) -> int:
    from typekernel.cli.proof_cmd import PROOF_SETS, proof_project

    tokens = list(getattr(args, "tokens", []) or [])
    proof_set = None
    path = "."
    if tokens:
        if tokens[0] in PROOF_SETS:
            proof_set = tokens[0]
            if len(tokens) > 1:
                path = tokens[1]
            if len(tokens) > 2:
                print(
                    "error: too many positional args; expected [SET] [PATH]",
                    file=sys.stderr,
                )
                return 2
        else:
            # Bare project path with --text/--glyph (or mistaken SET).
            if len(tokens) == 1:
                path = tokens[0]
            else:
                print(
                    f"error: unknown proof set {tokens[0]!r}; choose from {PROOF_SETS}",
                    file=sys.stderr,
                )
                return 2

    if proof_set is None and not args.text and not args.glyph:
        print(
            "error: need a proof set (control|spacing|kern|charset|ladder|all) "
            "or --text / --glyph",
            file=sys.stderr,
        )
        return 2
    paths = proof_project(
        path,
        proof_set,
        out_dir=args.out,
        build_dir=args.build_dir,
        text=args.text,
        glyph=args.glyph,
        size=args.size,
    )
    for p in paths:
        print(p)
    return 0


def _cmd_audit(args: argparse.Namespace) -> int:
    from typekernel.cli.audit import audit_project, format_report

    report = audit_project(
        args.path,
        check_stem=not args.no_stem,
        check_zone=not args.no_zone,
        check_direction=not args.no_direction,
        check_compat=args.compat or not args.no_compat,
        check_overlap=bool(getattr(args, "overlap", False)),
    )
    print(format_report(report))
    return 1 if report.errors else 0


def _cmd_pen(args: argparse.Namespace) -> int:
    from typekernel.cli.pen_cmd import render_pen_preview

    path = render_pen_preview(
        contrast=args.contrast,
        angle_deg=args.angle,
        thickness=args.thickness,
        out=args.out,
    )
    print(path)
    return 0


def _cmd_diff(args: argparse.Namespace) -> int:
    from typekernel.cli.diff_cmd import (
        DEFAULT_SNAPSHOT_NAME,
        diff_project,
        format_diff,
        write_snapshot,
    )

    root = Path(args.path).resolve()
    if args.snapshot is not None:
        dest = (
            root / "build" / DEFAULT_SNAPSHOT_NAME
            if args.snapshot == ""
            else Path(args.snapshot)
        )
        path = write_snapshot(root, dest, master=args.master)
        import json

        n = len(json.loads(path.read_text(encoding="utf-8"))["glyphs"])
        print(f"wrote {path}")
        print(f"snapshot glyphs: {n}")
        return 0
    result = diff_project(root, against=args.against, master=args.master)
    print(format_diff(result))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tk",
        description="typekernel project tools (ARCHITECTURE.md「标准工作流」)",
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
        help="starter template: omit/empty, or latin-sans | latin-humanist-italic | latin-chancery",
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
    p_build.add_argument(
        "--variable",
        action="store_true",
        help="build Light/Regular/Bold masters and a variable font (wght)",
    )
    p_build.add_argument(
        "--resolve-overlaps",
        action="store_true",
        dest="resolve_overlaps",
        help=(
            "static ship only: ufo2ft removeOverlaps at compile time "
            "(packaging; not a design-time seal). Incompatible with --variable"
        ),
    )
    p_build.set_defaults(func=_cmd_build)

    p_proof = sub.add_parser("proof", help="render proof PNGs from the built font")
    p_proof.add_argument(
        "tokens",
        nargs="*",
        default=[],
        metavar="SET|PATH",
        help="optional SET (control|spacing|kern|charset|ladder|all) then PATH "
        "(default PATH=.); omit SET when using only --text / --glyph",
    )
    p_proof.add_argument(
        "--text",
        default=None,
        help="render an arbitrary proof string to proofs/text.png",
    )
    p_proof.add_argument(
        "--glyph",
        default=None,
        help="zoom one character (or short cluster) to proofs/glyph-*.png",
    )
    p_proof.add_argument(
        "--size",
        type=int,
        default=None,
        help="pixel size for --text / --glyph / control (defaults vary by mode)",
    )
    p_proof.add_argument("--out", default=None, help="PNG output directory")
    p_proof.add_argument(
        "--build-dir",
        default=None,
        help="directory with OTF/TTF (default: <project>/build)",
    )
    p_proof.set_defaults(func=_cmd_proof)

    p_audit = sub.add_parser("audit", help="stem / zone / direction / compat diagnostics")
    p_audit.add_argument(
        "path",
        nargs="?",
        default=".",
        help="project root (default: .)",
    )
    p_audit.add_argument("--compat", action="store_true", help="force master compat check")
    p_audit.add_argument("--no-compat", action="store_true", help="skip master compat")
    p_audit.add_argument("--no-stem", action="store_true")
    p_audit.add_argument("--no-zone", action="store_true")
    p_audit.add_argument("--no-direction", action="store_true")
    p_audit.add_argument(
        "--overlap",
        action="store_true",
        help="opt-in: warn when ink∩ink cancel adjoins a counter (cavity notch)",
    )
    p_audit.set_defaults(func=_cmd_audit)

    p_pen = sub.add_parser(
        "pen",
        help="preview broad-nib contrast×angle (effective width by stroke direction)",
    )
    p_pen.add_argument("--contrast", type=float, default=0.55, help="ellipse axis ratio")
    p_pen.add_argument("--angle", type=float, default=30.0, help="pen rotation degrees")
    p_pen.add_argument("--thickness", type=float, default=100.0, help="vertical stroke width")
    p_pen.add_argument(
        "--out",
        default="pen_preview.png",
        help="PNG path (default: pen_preview.png)",
    )
    p_pen.set_defaults(func=_cmd_pen)

    p_diff = sub.add_parser(
        "diff",
        help="list glyphs whose outlines/advances changed (outline_hash)",
    )
    p_diff.add_argument(
        "path",
        nargs="?",
        default=".",
        help="project root (default: .)",
    )
    p_diff.add_argument(
        "--against",
        default=None,
        help="baseline: glyph_hashes.json or another project root "
        "(default: <project>/build/glyph_hashes.json)",
    )
    p_diff.add_argument(
        "--snapshot",
        nargs="?",
        const="",
        default=None,
        help="write current glyph hashes JSON "
        "(default path: <project>/build/glyph_hashes.json)",
    )
    p_diff.add_argument(
        "--master",
        default=None,
        help="optional Project master name for evaluation",
    )
    p_diff.set_defaults(func=_cmd_diff)

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

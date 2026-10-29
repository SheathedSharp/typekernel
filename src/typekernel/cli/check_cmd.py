"""``tk check --release`` — H-class + optional FontBakery (P4-7)."""

from __future__ import annotations

from pathlib import Path

from typekernel.cli.build import build_project
from typekernel.diagnose.release import (
    check_release,
    format_release_report,
    write_release_manifest,
)

__all__ = ["check_release_project"]


def check_release_project(
    root: str | Path,
    *,
    binary: str | Path | None = None,
    out_dir: str | Path | None = None,
    fontbakery: bool = True,
    build_if_missing: bool = True,
) -> tuple[int, Path | None]:
    """Run release checks; return ``(exit_code, manifest_path)``.

    Exit 0 when H errors == 0 and FontBakery FAIL == 0 (or FontBakery skipped).
    """
    root_path = Path(root).resolve()
    build_dir = Path(out_dir) if out_dir else root_path / "build"

    if binary is not None:
        bin_path = Path(binary)
    else:
        bin_path = None
        for pattern in ("*.ttf", "*.otf"):
            found = sorted(build_dir.glob(pattern))
            # Prefer non-VF static for H checks when both exist.
            statics = [p for p in found if "-VF" not in p.name]
            pick = statics or found
            if pick:
                bin_path = pick[0]
                break
        if bin_path is None and build_if_missing:
            _font, built = build_project(root_path, out_dir=build_dir, formats=("ttf",))
            bin_path = built.binaries.get("ttf") or next(iter(built.binaries.values()), None)
        if bin_path is None:
            raise FileNotFoundError(f"no font binary under {build_dir}")

    report = check_release(bin_path, fontbakery=fontbakery)
    print(format_release_report(report), end="")
    manifest = write_release_manifest(
        report,
        Path(bin_path).with_suffix(Path(bin_path).suffix + ".release.json"),
    )
    print(f"manifest: {manifest}")
    fb_fail = report.fontbakery_fail_count if report.fontbakery else 0
    if report.error_count or fb_fail:
        return 1, manifest
    return 0, manifest

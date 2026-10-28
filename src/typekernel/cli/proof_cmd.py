"""``tk proof`` — render proof sheets via :mod:`typekernel.qa.proof`."""

from __future__ import annotations

from pathlib import Path

from typekernel.cli.build import build_project
from typekernel.qa.proof import (
    proof_charset_grid,
    proof_context,
    proof_kern_pairs,
    proof_sheet,
    proof_spacing_strings,
)

__all__ = ["PROOF_SETS", "proof_project"]

# Default control string from ARCHITECTURE.md 验收方式 (user projects may override).
_CONTROL_TEXT = "nnonoo nnhnnhnn oobobboo HHOHOO HOHHOO"

PROOF_SETS = ("control", "spacing", "kern", "charset", "all")


def _find_binary(root: Path, build_dir: Path) -> Path:
    for pattern in ("*.otf", "*.ttf"):
        found = sorted(build_dir.glob(pattern))
        if found:
            return found[0]
    # Build on demand.
    _font, result = build_project(root, out_dir=build_dir, formats=("otf",))
    binaries = result.binaries
    if "otf" in binaries:
        return binaries["otf"]
    if binaries:
        return next(iter(binaries.values()))
    raise FileNotFoundError(f"no font binary under {build_dir}")


def proof_project(
    root: str | Path,
    proof_set: str,
    *,
    out_dir: str | Path | None = None,
    build_dir: str | Path | None = None,
) -> list[Path]:
    """Render ``proof_set`` for the project; return written PNG paths."""
    if proof_set not in PROOF_SETS:
        raise ValueError(f"unknown proof set {proof_set!r}; choose from {PROOF_SETS}")

    root_path = Path(root).resolve()
    bdir = Path(build_dir) if build_dir is not None else root_path / "build"
    odir = Path(out_dir) if out_dir is not None else root_path / "proofs"
    odir.mkdir(parents=True, exist_ok=True)
    binary = _find_binary(root_path, bdir)

    written: list[Path] = []
    if proof_set in ("control", "all"):
        written.append(
            proof_context(binary, _CONTROL_TEXT, odir / "control.png", size=36)
        )
    if proof_set in ("spacing", "all"):
        written.append(proof_spacing_strings(binary, odir / "spacing.png"))
    if proof_set in ("kern", "all"):
        written.append(proof_kern_pairs(binary, odir / "kern.png"))
    if proof_set in ("charset", "all"):
        written.append(proof_charset_grid(binary, odir / "charset.png"))
    if proof_set == "all":
        # Combined sheet as well.
        written.append(proof_sheet(binary, odir / "sheet.png", context_text=_CONTROL_TEXT))
    return written

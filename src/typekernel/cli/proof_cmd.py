"""``tk proof`` — render proof sheets via :mod:`typekernel.qa.proof`."""

from __future__ import annotations

from pathlib import Path

from typekernel.cli.build import build_project
from typekernel.qa.proof import (
    proof_charset_grid,
    proof_context,
    proof_glyph,
    proof_kern_pairs,
    proof_sheet,
    proof_spacing_strings,
    proof_weight_ladder,
)

__all__ = ["PROOF_SETS", "proof_project"]

# Default control string from ARCHITECTURE.md 验收方式 (user projects may override).
_CONTROL_TEXT = "nnonoo nnhnnhnn oobobboo HHOHOO HOHHOO"
_LADDER_TEXT = "nnonoo HHOHOO hamburgefonstiv"

PROOF_SETS = ("control", "spacing", "kern", "charset", "ladder", "all")


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


def _find_variable_binary(build_dir: Path) -> Path | None:
    """Prefer a variable font when present (``*VF*`` then any binary with fvar).

    ``tk build --variable`` defaults to OTF, so both extensions must be
    considered; checking only ``*.ttf`` silently fell back to a static
    single-weight ladder.
    """
    candidates = (
        sorted(build_dir.glob("*VF*.ttf"))
        + sorted(build_dir.glob("*VF*.otf"))
        + sorted(build_dir.glob("*.ttf"))
        + sorted(build_dir.glob("*.otf"))
    )
    for path in candidates:
        try:
            from fontTools.ttLib import TTFont

            tt = TTFont(path)
            if "fvar" in tt:
                tt.close()
                return path
            tt.close()
        except Exception:  # noqa: BLE001, S112 - skip non-fonts in the build dir
            continue
    return None


def proof_project(
    root: str | Path,
    proof_set: str | None = None,
    *,
    out_dir: str | Path | None = None,
    build_dir: str | Path | None = None,
    text: str | None = None,
    glyph: str | None = None,
    size: int | None = None,
    control_text: str | None = None,
) -> list[Path]:
    """Render proof outputs for the project; return written PNG paths.

    ``proof_set`` selects a canned sheet (``control`` / ``spacing`` / …).
    ``text`` and ``glyph`` are free-form designer views (any string / zoomed
    character) and may be combined with a set. At least one of ``proof_set``,
    ``text``, or ``glyph`` is required.
    """
    if proof_set is None and text is None and glyph is None:
        raise ValueError(
            "need a proof set (control|spacing|kern|charset|ladder|all) "
            "or --text / --glyph"
        )
    if proof_set is not None and proof_set not in PROOF_SETS:
        raise ValueError(f"unknown proof set {proof_set!r}; choose from {PROOF_SETS}")

    root_path = Path(root).resolve()
    bdir = Path(build_dir) if build_dir is not None else root_path / "build"
    odir = Path(out_dir) if out_dir is not None else root_path / "proofs"
    odir.mkdir(parents=True, exist_ok=True)
    binary = _find_binary(root_path, bdir)
    ctrl = control_text if control_text is not None else _CONTROL_TEXT

    written: list[Path] = []
    if text is not None:
        written.append(
            proof_context(
                binary,
                text,
                odir / "text.png",
                size=size if size is not None else 48,
            )
        )
    if glyph is not None:
        written.append(
            proof_glyph(
                binary,
                glyph,
                odir / f"glyph-{_safe_name(glyph)}.png",
                size=size if size is not None else 240,
            )
        )
    if proof_set in ("control", "all"):
        written.append(
            proof_context(
                binary,
                ctrl,
                odir / "control.png",
                size=size if size is not None else 36,
            )
        )
    if proof_set in ("spacing", "all"):
        written.append(proof_spacing_strings(binary, odir / "spacing.png"))
    if proof_set in ("kern", "all"):
        written.append(proof_kern_pairs(binary, odir / "kern.png"))
    if proof_set in ("charset", "all"):
        written.append(proof_charset_grid(binary, odir / "charset.png"))
    if proof_set in ("ladder", "all"):
        vf = _find_variable_binary(bdir)
        if vf is None:
            # Static fallback: single-weight ladder still useful as a phrase sheet.
            written.append(
                proof_context(
                    binary,
                    _LADDER_TEXT,
                    odir / "ladder.png",
                    size=size if size is not None else 56,
                )
            )
        else:
            written.append(
                proof_weight_ladder(
                    vf,
                    text if text is not None else _LADDER_TEXT,
                    odir / "ladder.png",
                    size=size if size is not None else 56,
                )
            )
    if proof_set == "all":
        written.append(proof_sheet(binary, odir / "sheet.png", context_text=ctrl))
    return written


def _safe_name(glyph: str) -> str:
    """Filesystem-safe fragment for ``glyph-*.png``."""
    out = []
    for ch in glyph:
        if ch.isalnum() or ch in "-_":
            out.append(ch)
        else:
            out.append(f"u{ord(ch):04x}")
    return "".join(out) or "glyph"

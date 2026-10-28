"""Static ``resolve_overlaps`` is packaging, not a design-time seal."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("ufoLib2")
pytest.importorskip("ufo2ft")

from typekernel.compile.build import build_ttf_from_ufo
from typekernel.compile.ufo_export import write_outline_to_ufo
from typekernel.geo.path_builder import PathBuilder


def _overlapping_ink():
    """Two overlapping rectangles (union should become one contour)."""
    b = PathBuilder()
    b.moveTo(0, 0)
    b.lineTo(100, 0)
    b.lineTo(100, 100)
    b.lineTo(0, 100)
    b.closePath()
    b.moveTo(50, 50)
    b.lineTo(150, 50)
    b.lineTo(150, 150)
    b.lineTo(50, 150)
    b.closePath()
    return b.build()


def test_resolve_overlaps_recorded_in_manifest(tmp_path: Path) -> None:
    ufo = tmp_path / "Ov.ufo"
    ttf = tmp_path / "Ov.ttf"
    write_outline_to_ufo(_overlapping_ink(), ufo, glyph_name="O")
    quiet = build_ttf_from_ufo(ufo, tmp_path / "quiet.ttf", resolve_overlaps=False)
    assert quiet.filters == ()
    resolved = build_ttf_from_ufo(ufo, ttf, resolve_overlaps=True)
    assert resolved.filters == ("resolve_overlaps",)
    assert ttf.is_file()


def test_cli_rejects_resolve_with_variable(tmp_path: Path) -> None:
    import subprocess
    import sys

    from typekernel.cli.new import create_project

    root = create_project("vfov", parent=tmp_path, starter="latin-sans")
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "typekernel.cli",
            "build",
            str(root),
            "--variable",
            "--resolve-overlaps",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    assert "static-export only" in proc.stderr

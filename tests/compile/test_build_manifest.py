"""TTF build runner and BuildManifest recording."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("ufoLib2")
pytest.importorskip("ufo2ft")
# fontmake is optional for the runner (ufo2ft path); skip-friendly if absent
fontmake = pytest.importorskip("fontmake")

from fontTools.ttLib import TTFont

from typekernel.compile.build import BuildManifest, build_ttf_from_ufo
from typekernel.compile.ufo_export import write_outline_to_ufo
from typekernel.geo.path_builder import PathBuilder


def _outline():
    b = PathBuilder()
    b.moveTo(50, 0)
    b.lineTo(150, 0)
    b.lineTo(150, 200)
    b.lineTo(50, 200)
    b.closePath()
    return b.build()


def test_build_ttf_writes_file_and_manifest(tmp_path: Path) -> None:
    ufo_path = tmp_path / "Build.ufo"
    ttf_path = tmp_path / "Build.ttf"
    manifest_path = tmp_path / "Build.manifest.json"

    write_outline_to_ufo(_outline(), ufo_path, glyph_name="B")
    manifest = build_ttf_from_ufo(ufo_path, ttf_path, manifest_path=manifest_path)

    assert ttf_path.is_file()
    assert ttf_path.stat().st_size > 0
    assert isinstance(manifest, BuildManifest)
    assert manifest.filters == ()
    assert manifest.output_format == "ttf"
    assert manifest.ufo2ft_version is not None
    assert manifest.fonttools_version is not None
    # fontmake recorded when installed (this test importorskip'd it)
    assert manifest.fontmake_version is not None

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["filters"] == []
    assert data["inputs"]["ufo"] == str(ufo_path)

    # Readable TrueType
    font = TTFont(ttf_path)
    assert "glyf" in font or "CFF " in font
    font.close()


def test_build_manifest_to_json_roundtrip() -> None:
    m = BuildManifest(
        fonttools_version="4.0",
        fontmake_version=None,
        ufo2ft_version="3.0",
        timestamp="2026-01-01T00:00:00+00:00",
        inputs={"ufo": "a.ufo", "output": "a.ttf"},
        filters=(),
        output_format="ttf",
    )
    data = m.to_json()
    assert data["filters"] == []
    assert data["fontmake_version"] is None

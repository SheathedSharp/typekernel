"""Tests for weight-axis designspace export."""

from __future__ import annotations

from pathlib import Path

import pytest
from fontTools.designspaceLib import DesignSpaceDocument

from typekernel.axes.designspace_export import write_weight_designspace


def test_writes_designspace_with_wght(tmp_path: Path) -> None:
    out = tmp_path / "weight.designspace"
    write_weight_designspace(
        out,
        axis_min=400,
        axis_max=700,
        sources=(
            ("Regular", 400.0, "masters/Regular.ufo"),
            ("Bold", 700.0, "masters/Bold.ufo"),
        ),
    )
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert "wght" in text

    document = DesignSpaceDocument.fromfile(out)
    assert len(document.axes) == 1
    assert document.axes[0].tag == "wght"
    assert document.axes[0].minimum == 400
    assert document.axes[0].maximum == 700
    assert len(document.sources) == 2
    assert document.sources[0].filename == "masters/Regular.ufo"
    assert document.sources[1].location == {"weight": 700.0}


def test_empty_sources_raise(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="at least one source"):
        write_weight_designspace(tmp_path / "empty.designspace", 400, 700, sources=())

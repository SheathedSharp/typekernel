"""latin-sans wght 100–900 VF, STAT, nine named instances."""

from __future__ import annotations

from pathlib import Path

import pytest
from fontTools.designspaceLib import DesignSpaceDocument
from fontTools.ttLib import TTFont


pytest.importorskip("ufo2ft")


def test_latin_sans_vf_axis_instances_stat(tmp_path: Path) -> None:
    from typekernel.cli.build import build_variable_project
    from typekernel.project import open_project

    root = Path(__file__).resolve().parents[2] / "src/typekernel/starters/latin_sans"
    with open_project(root) as session:
        assert session.project.axes[0].minimum == 100.0
        assert session.project.axes[0].maximum == 900.0
        assert len(session.project.instances) == 9

    _masters, vf = build_variable_project(root, out_dir=tmp_path, formats=("ttf",))
    doc = DesignSpaceDocument.fromfile(vf.designspace)
    assert doc.axes[0].tag == "wght"
    assert doc.axes[0].minimum == 100.0
    assert doc.axes[0].maximum == 900.0
    assert len(doc.axes[0].axisLabels or []) == 9
    assert [i.styleName for i in doc.instances] == [
        "Thin",
        "ExtraLight",
        "Light",
        "Regular",
        "Medium",
        "SemiBold",
        "Bold",
        "ExtraBold",
        "Black",
    ]
    assert len(vf.static_instances) == 9

    tt = TTFont(vf.binaries["ttf"])
    assert "fvar" in tt and "STAT" in tt
    axis = tt["fvar"].axes[0]
    assert axis.axisTag == "wght"
    assert axis.minValue == 100.0
    assert axis.maxValue == 900.0
    assert len(tt["fvar"].instances) == 9

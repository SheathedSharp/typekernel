"""AE digraph letter-class: topology stable; read tops AE when intended."""

from __future__ import annotations

from pathlib import Path

from typekernel.perceive.read import read_glyph
from typekernel.perceive.topology import measure_topology
from typekernel.project import open_project

ROOT = Path(__file__).resolve().parents[2] / "src/typekernel/starters/latin_sans"


def test_ae_topology_stable_across_masters() -> None:
    with open_project(ROOT) as session:
        for master in (None, "Light", "Bold"):
            g = session.glyph("AE", master=master)
            system = session.project.system
            if master is not None:
                by = {m.name: m for m in session.project.masters}
                system = by[master].system
            stem = float(system.stem.get("uc", 80.0))
            topo = measure_topology(g.outline, stem=stem)
            assert topo.counters == 1
            assert topo.islands == 1


def test_ae_read_tops_intended() -> None:
    with open_project(ROOT) as session:
        report = read_glyph(session, "AE", intended_cp=0x00C6)
    assert report.top
    assert report.top[0].name == "AE"
    assert not any(w.level == "warn" for w in report.warnings)

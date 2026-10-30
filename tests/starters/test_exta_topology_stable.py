"""Ext-A clear letter-class topology: master-stable where we claimed fixes."""

from __future__ import annotations

from pathlib import Path

from typekernel.perceive.topology import measure_topology
from typekernel.project import open_project

ROOT = Path(__file__).resolve().parents[2] / "src/typekernel/starters/latin_sans"

# name → (counters, islands) expected on Light and Bold
_STABLE = {
    "Eth": (1, 1),
    "dcroat": (1, 1),
    "hbar": (0, 1),
    "IJ": (0, 2),
    "ij": (0, 4),
    "AE": (1, 1),
}


def test_exta_claimed_glyphs_stable_across_masters() -> None:
    with open_project(ROOT) as session:
        for name, (counters, islands) in _STABLE.items():
            for master in ("Light", "Bold"):
                g = session.glyph(name, master=master)
                by = {m.name: m for m in session.project.masters}
                system = by[master].system
                stem = float(next(iter(system.stem.values()), 80.0))
                topo = measure_topology(g.outline, stem=stem)
                assert topo.counters == counters, (name, master, topo)
                assert topo.islands == islands, (name, master, topo)
                assert topo.slit_counters == 0, (name, master, topo)

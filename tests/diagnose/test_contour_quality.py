"""S0 contour quality: bloated polylines surface visible warns."""

from __future__ import annotations

from typekernel.diagnose.checks.contour import ContourQualityCheck, defect_visible
from typekernel.diagnose.protocol import CheckContext
from typekernel.draw import Writer
from typekernel.system import Overshoot, System, Zones


def _system() -> System:
    return System(
        upm=1000,
        zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),
        overshoot=Overshoot(round=12, pointed=10),
        stem={"lc": 80},
    )


def _bloated_circle(n: int = 120):
    """Polyline-ish closed path with many short segments (junk expansion)."""
    import math

    w = Writer()
    r = 200.0
    for i in range(n):
        ang = 2 * math.pi * i / n
        x, y = 300 + r * math.cos(ang), 300 + r * math.sin(ang)
        if i == 0:
            w = w.start((x, y))
        else:
            w = w.line((x, y))
    return w.close().build()


def test_defect_visible_scales() -> None:
    assert defect_visible(50.0, 1000.0) is True
    assert defect_visible(0.01, 1000.0) is False


def test_bloated_contour_warns_on_node_budget() -> None:
    drawing = _bloated_circle(120)
    sys = _system()

    class _S:
        def specs(self):
            return {}

        def glyph(self, name, master=None):
            raise KeyError(name)

    sess = _S()
    ctx = CheckContext(
        session=sess,  # type: ignore[arg-type]
        project=sess,  # type: ignore[arg-type]
        system=sys,
        name="o",
        raw=drawing,
        final=drawing,
        stem_kinds={},
    )
    out = list(ContourQualityCheck().run(ctx))
    node_findings = [f for f in out if f.check == "contour.nodes"]
    assert node_findings, out
    assert any(f.level == "warn" for f in node_findings), node_findings

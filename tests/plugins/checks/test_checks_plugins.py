"""plugins.checks are callable and EXTRA_CHECKS hooks into tk audit."""

from __future__ import annotations

from pathlib import Path

from typekernel.cli.audit import audit_project
from typekernel.cli.new import create_project
from typekernel.draw import Drawing, Writer
from typekernel.geo.contour import reverse_contour
from typekernel.plugins.checks import builtin_checks, direction
from typekernel.plugins.checks.protocol import CheckContext, Finding
from typekernel.system import Overshoot, System, Zones


def test_builtin_checks_flags() -> None:
    assert len(builtin_checks()) >= 3
    assert len(builtin_checks(check_overlap=True)) == len(builtin_checks()) + 1


def test_extra_checks_from_system(tmp_path: Path) -> None:
    root = create_project("extracheck", parent=tmp_path, starter="latin-sans")
    sys_py = root / "system.py"
    sys_py.write_text(
        sys_py.read_text(encoding="utf-8")
        + """

def _mark_n(ctx):
    if ctx.name == "n":
        from typekernel.plugins.checks.protocol import Finding
        ctx.findings.append(Finding("custom", "warn", "n", "extra-check-fired"))

EXTRA_CHECKS = (_mark_n,)
""",
        encoding="utf-8",
    )
    report = audit_project(root, glyphs=["n"])
    assert any(f.message == "extra-check-fired" for f in report.findings)


def test_direction_plugin_flags_cw_ink() -> None:
    ccw = (
        Writer()
        .start((0, 0))
        .line((100, 0))
        .line((100, 100))
        .line((0, 100))
        .close()
        .build()
    )
    d = Drawing((reverse_contour(ccw.contours[0]),), ("ink",), ((),), slots=())
    system = System(
        upm=1000,
        stem={"lc": 70.0},
        zones=Zones(x=500, cap=700, asc=750, desc=-200, base=0),
        overshoot=Overshoot(round=12, pointed=8),
    )

    class _P:
        masters = ()

        def specs(self):
            return {}

    proj = _P()
    proj.system = system  # type: ignore[attr-defined]
    findings: list[Finding] = []
    ctx = CheckContext(
        name="x",
        raw=d,
        final=d,
        system=system,
        project=proj,  # type: ignore[arg-type]
        stem_kinds={},
        findings=findings,
    )
    direction.check(ctx)
    assert any(f.kind == "direction" and f.level == "error" for f in findings)

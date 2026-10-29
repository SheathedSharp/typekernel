"""Stem-kind policy: suppress vertical optical noise; honor AUDIT_STEMS."""

from __future__ import annotations

from pathlib import Path

import pytest

from typekernel.cli.audit import audit_project, load_audit_stems
from typekernel.cli.new import create_project
from typekernel.draw import Writer
from typekernel.geo.point import Point
from typekernel.optics.stem import measure_oriented_stem, vertical_equiv_from_diagonal


def test_latin_sans_default_audit_quiet(tmp_path: Path) -> None:
    root = create_project("quiet", parent=tmp_path, starter="latin-sans")
    report = audit_project(root)
    assert report.errors == []
    # Structural starter: B/C/E/F-class warnings are expected after P2 diagnose.
    expected = ("topology.", "vertical.", "spacing.", "gray.", "interpolation.")
    unexpected = [
        f for f in report.warnings if not f.check.startswith(expected)
    ]
    assert unexpected == [], unexpected
    assert any(f.check.startswith("topology.") for f in report.warnings)


def test_audit_stems_none_skips_optical(tmp_path: Path) -> None:
    root = create_project("kinds", parent=tmp_path, starter="latin-sans")
    sys_py = root / "system.py"
    text = sys_py.read_text(encoding="utf-8")
    text += "\n\nAUDIT_STEMS = {\"n\": \"none\", \"v\": (\"diagonal\",)}\n"
    sys_py.write_text(text, encoding="utf-8")
    kinds = load_audit_stems(root)
    assert kinds["n"] == ()
    assert kinds["v"] == ("diagonal",)
    report = audit_project(root)
    assert report.errors == []


def test_measure_oriented_stem_on_diagonal_band() -> None:
    """Synthetic thick diagonal: oriented probe recovers target thickness."""
    # Build a filled parallelogram ~100 thick along 45° by Writer polygon.
    # Band from (0,0)-(200,200) with perp half-width 50.
    import math

    ux = uy = math.sqrt(0.5)
    nx, ny = -uy, ux
    half = 50.0
    p0 = Point(40, 40)
    p1 = Point(240, 240)
    a = Point(p0.x + nx * half, p0.y + ny * half)
    b = Point(p1.x + nx * half, p1.y + ny * half)
    c = Point(p1.x - nx * half, p1.y - ny * half)
    d = Point(p0.x - nx * half, p0.y - ny * half)
    drawing = (
        Writer()
        .start((a.x, a.y))
        .line((b.x, b.y))
        .line((c.x, c.y))
        .line((d.x, d.y))
        .close()
        .build()
    )
    outline = drawing.outline()
    mid = ((a.x + c.x) / 2, (a.y + c.y) / 2)
    w = measure_oriented_stem(outline, mid, 45.0)
    assert w is not None
    assert abs(w - 100.0) < 2.0
    equiv = vertical_equiv_from_diagonal(w, angle_from_vertical_deg=45.0)
    assert equiv > w  # compensated upright equivalent is thicker


def test_overlap_check_opt_in(tmp_path: Path) -> None:
    pytest.importorskip("pathops")  # typekernel[boolean]
    root = create_project("ov", parent=tmp_path, starter="latin-sans")
    quiet = audit_project(
        root,
        check_overlap=False,
        check_topology=False,
        check_vertical=False,
        check_spacing=False,
        check_gray=False,
        check_interpolation=False,
    )
    noisy = audit_project(
        root,
        check_overlap=True,
        check_topology=False,
        check_vertical=False,
        check_spacing=False,
        check_gray=False,
        check_interpolation=False,
    )
    assert quiet.warnings == []
    assert any(f.kind == "overlap" for f in noisy.warnings)


def test_declared_diagonal_is_warn_empty_is_quiet() -> None:
    """Empty kinds stay quiet; declared ("diagonal",) opts into stem warnings."""
    import math

    from unittest.mock import MagicMock

    from typekernel.plugins.checks import stem as stem_check
    from typekernel.plugins.checks.protocol import CheckContext
    from typekernel.system import Overshoot, System, Zones

    # Thick 45° parallelogram (~100) vs System lc=50 → clear diagonal miss.
    ux = uy = math.sqrt(0.5)
    nx, ny = -uy, ux
    # Width ~60 vs System lc=50: within optical accept band, above warn tol.
    half = 30.0
    p0, p1 = Point(40, 40), Point(240, 240)
    a = Point(p0.x + nx * half, p0.y + ny * half)
    b = Point(p1.x + nx * half, p1.y + ny * half)
    c = Point(p1.x - nx * half, p1.y - ny * half)
    d = Point(p0.x - nx * half, p0.y - ny * half)
    drawing = (
        Writer()
        .start((a.x, a.y))
        .line((b.x, b.y))
        .line((c.x, c.y))
        .line((d.x, d.y))
        .close()
        .build()
    )
    system = System(
        upm=1000,
        zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),
        overshoot=Overshoot(round=12, pointed=10),
        stem={"lc": 70, "uc": 70},
    )

    quiet_ctx = CheckContext(
        name="diag",
        raw=drawing,
        final=drawing,
        system=system,
        project=MagicMock(),
        stem_kinds={"diag": ()},
        declared_stems={"diag": ()},
        findings=[],
    )
    stem_check.check(quiet_ctx)
    assert not [f for f in quiet_ctx.findings if f.kind == "stem"]

    warn_ctx = CheckContext(
        name="diag",
        raw=drawing,
        final=drawing,
        system=system,
        project=MagicMock(),
        stem_kinds={"diag": ("diagonal",)},
        declared_stems={"diag": ("diagonal",)},
        findings=[],
    )
    stem_check.check(warn_ctx)
    declared = [f for f in warn_ctx.findings if f.kind == "stem"]
    assert any(f.level == "warn" for f in declared), declared

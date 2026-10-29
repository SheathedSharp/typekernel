"""vertical reach, gray outliers, spacing fixtures."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from typekernel.cli.new import create_project
from typekernel.diagnose import audit_project
from typekernel.diagnose.checks.vertical import VerticalCheck
from typekernel.diagnose.protocol import CheckContext
from typekernel.draw import Writer
from typekernel.project import open_project
from typekernel.project.registry import GlyphSpec


def test_appendix_a7_reach_on_latin_sans() -> None:
    """Expect table matches structural reach (J hook / question bowl)."""
    td = Path(tempfile.mkdtemp())
    try:
        root = create_project("reach", parent=td, starter="latin-sans")
        report = audit_project(root, glyphs=["J", "question", "n"])
        reach = [f for f in report.findings if f.check == "vertical.reach"]
        glyphs = {f.glyph for f in reach}
        assert "J" not in glyphs, reach
        assert "question" not in glyphs, reach
        assert "n" not in glyphs, reach
    finally:
        shutil.rmtree(td)


def test_overshoot_fixture_too_big() -> None:
    td = Path(tempfile.mkdtemp())
    try:
        root = create_project("ovshoot", parent=td, starter="latin-sans")
        with open_project(root) as session:
            system = session.project.system
            ovr = float(system.overshoot.round)
            top = system.zones.x + 5 * ovr
            drawing = (
                Writer()
                .start((0, 0))
                .line((200, 0))
                .line((200, top))
                .line((0, top))
                .close()
                .build()
            )
            session._specs["synth_round"] = GlyphSpec(
                name="synth_round",
                group="test",
                build=lambda _s: drawing,
                masters={},
                traits=("x-height", "round-top"),
            )
            ctx = CheckContext(
                session=session,
                project=session.project,
                system=system,
                name="synth_round",
                raw=drawing,
                final=drawing,
            )
            findings = list(VerticalCheck().run(ctx))
            assert any(f.check == "vertical.overshoot" for f in findings), findings
    finally:
        shutil.rmtree(td)


def test_gray_narrow_stems_not_false_letter_outliers() -> None:
    """Tall thin stems compare in a .narrow cohort — not vs n/o letter gray."""
    td = Path(tempfile.mkdtemp())
    try:
        root = create_project("gray", parent=td, starter="latin-sans")
        report = audit_project(root)
        gray = [f for f in report.findings if f.check == "gray.density" and f.level == "warn"]
        glyphs = {f.glyph for f in gray}
        assert "parenleft" not in glyphs and "parenright" not in glyphs, glyphs
        assert len(gray) <= 5, glyphs
    finally:
        shutil.rmtree(td)

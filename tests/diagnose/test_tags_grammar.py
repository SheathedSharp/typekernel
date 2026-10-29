"""tags.grammar info check."""

from __future__ import annotations

from pathlib import Path

from typekernel.diagnose.checks.tags import TagsGrammarCheck
from typekernel.diagnose.engine import audit_project
from typekernel.draw import Writer
from typekernel.project import open_project

STARTER = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "typekernel"
    / "starters"
    / "latin_sans"
)


def test_tags_grammar_check_flags_bad_synthetic() -> None:
    drawing = (
        Writer()
        .start((0.0, 0.0))
        .corner("arm.l.bot")
        .line((0.0, 100.0))
        .corner("stem.l.top.o")
        .line((40.0, 100.0))
        .line((40.0, 0.0))
        .line((0.0, 0.0))
        .close()
        .build()
    )
    # Exercise the check against a fake context via protocol fields.
    from typekernel.diagnose.protocol import CheckContext
    from typekernel.system import Overshoot, System, Zones

    system = System(
        upm=1000,
        zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),
        overshoot=Overshoot(round=12, pointed=10),
        stem={"lc": 80, "uc": 90},
    )
    with open_project(STARTER) as session:
        ctx = CheckContext(
            session=session,
            project=session.project,
            system=system,
            name="_synthetic",
            raw=drawing,
            final=drawing,
        )
        findings = list(TagsGrammarCheck().run(ctx))
    kinds = {(f.level, f.where) for f in findings}
    assert ("info", "arm.l.bot") in kinds
    assert ("info", "stem.l.top.o") not in kinds


def test_audit_emits_tags_grammar_info_on_latin_sans() -> None:
    report = audit_project(STARTER, glyphs=["H", "e", "n"], check_interpolation=False)
    tag_infos = [f for f in report.findings if f.check == "tags.grammar"]
    # H stem tags are legal; e / trough tags may still be debt.
    assert all(f.level == "info" for f in tag_infos)

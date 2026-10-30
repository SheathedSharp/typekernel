"""S2 tk read / identity classifier."""

from __future__ import annotations

from pathlib import Path

from typekernel.cli.new import create_project
from typekernel.cli.read_cmd import read_project
from typekernel.perceive.read import read_glyph, read_text
from typekernel.project import open_project

TRIAL = "zayju forever young"
TRIAL_LETTERS = sorted({c for c in TRIAL if c.isalpha()})


def test_trial_letters_are_twelve() -> None:
    assert len(TRIAL_LETTERS) == 12
    assert TRIAL_LETTERS == sorted("aefgjnoruvyz")


def test_z_drawn_as_e_warns(tmp_path: Path) -> None:
    """Cold-trial failure mode: intended z, measured e-like counters → hard warn."""
    root = create_project("read_ze", parent=tmp_path, starter="latin-sans")
    with open_project(root) as session:
        # Use the project's e outline but claim the intent was z.
        report = read_glyph(session, "e", intended_cp=ord("z"))
    assert report.top, report
    # Measured counters=1 → not z (0); top should be some counterful letter.
    assert report.top[0].codepoint != ord("z")
    assert any(w.level == "warn" for w in report.warnings), report.warnings
    assert any("confuse-pair" in w.message and "e" in w.message for w in report.warnings), (
        report.warnings
    )
    assert any(
        w.intended == "z" and "intended z" in w.message for w in report.warnings
    ), report.warnings


def test_trial_string_each_letter_has_read(tmp_path: Path) -> None:
    root = create_project("read_trial", parent=tmp_path, starter="latin-sans")
    with open_project(root) as session:
        reports = read_text(session, TRIAL)
    by_glyph = {r.glyph: r for r in reports}
    for ch in TRIAL_LETTERS:
        assert ch in by_glyph, ch
        assert by_glyph[ch].top, (ch, by_glyph[ch])


def test_tk_read_cli_text_exit(tmp_path: Path) -> None:
    root = create_project("read_cli", parent=tmp_path, starter="latin-sans")
    code, body = read_project(root, text="o")
    assert "o:" in body
    assert code in (0, 1)  # may warn if confuse; still returns a report

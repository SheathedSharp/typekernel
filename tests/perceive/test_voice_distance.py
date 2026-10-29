"""Structural voice_distance (not aesthetic originality)."""

from __future__ import annotations

from pathlib import Path

from typekernel.cli.new import create_project
from typekernel.perceive.voice import extract_voice, voice_distance
from typekernel.project import open_project


def test_voice_distance_self_is_zero(tmp_path: Path) -> None:
    root = create_project("voice_a", parent=tmp_path, starter="latin-sans")
    with open_project(root) as session:
        feat = extract_voice(session)
        assert voice_distance(feat, feat) == 0.0
        assert len(feat.rows) >= 5


def test_voice_distance_token_tweak_is_positive(tmp_path: Path) -> None:
    """Designed System stem change moves measurable features away from stock."""
    a = create_project("voice_stock", parent=tmp_path, starter="latin-sans")
    b = create_project("voice_heavy", parent=tmp_path, starter="latin-sans")
    sys_py = b / "system.py"
    text = sys_py.read_text(encoding="utf-8")
    text = text.replace('"lc": 84', '"lc": 120').replace("'lc': 84", "'lc': 120")
    sys_py.write_text(text, encoding="utf-8")
    with open_project(a) as sa, open_project(b) as sb:
        da = extract_voice(sa)
        db = extract_voice(sb)
        dist = voice_distance(da, db)
        assert dist > 0.0, (dist, da.rows.get("n"), db.rows.get("n"))

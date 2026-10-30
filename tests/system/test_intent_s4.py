"""S4 Intent tool / connection / genre."""

from __future__ import annotations

from typekernel.system import Intent
from typekernel.system.intent import pen_defaults_for, pen_for_intent


def test_tool_none_keeps_contrast_mapping() -> None:
    c, _a = pen_defaults_for(Intent(contrast="high"))
    assert abs(c - 0.28) < 1e-6


def test_pointed_tool_forces_near_circular() -> None:
    c, a = pen_defaults_for(Intent(tool="pointed", contrast="high", slant="italic", pen_angle_deg=28))
    assert c == 1.0
    assert a == 28.0
    pen = pen_for_intent(Intent(tool="pointed"), 60)
    assert pen.contrast == 1.0


def test_genre_roundhand_fields() -> None:
    intent = Intent(tool="pointed", connection="full", genre="roundhand", slant="italic")
    assert intent.genre == "roundhand"
    assert intent.connection == "full"

"""S3 curs / calt generation."""

from __future__ import annotations

from typekernel.features import generate_cursive_features, generate_features, validate_fea
from typekernel.font.glyph import Anchor


def test_calt_positional_forms() -> None:
    text = generate_features({"n", "n.init", "n.medi", "n.fina"})
    assert "feature calt" in text
    assert "n.init" in text
    validate_fea(text)


def test_curs_from_entry_exit() -> None:
    text = generate_cursive_features(
        {
            "n": (
                Anchor("entry", 10, 200),
                Anchor("exit", 390, 200),
            )
        }
    )
    assert "feature curs" in text
    assert "pos cursive n" in text
    validate_fea(text)

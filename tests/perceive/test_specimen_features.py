"""P2-11: features require uharfbuzz; clear ImportError."""

from __future__ import annotations

import pytest

from typekernel.perceive.specimen import proof_features


def test_features_without_uharfbuzz_is_clear(tmp_path, monkeypatch) -> None:
    import builtins

    real_import = builtins.__import__

    def _blocked(name, *args, **kwargs):
        if name == "uharfbuzz" or name.startswith("uharfbuzz."):
            raise ImportError("blocked for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _blocked)
    with pytest.raises(ImportError, match="uharfbuzz"):
        proof_features(tmp_path / "Missing.ttf", "Hi", tmp_path / "out.png", features=["kern"])

"""Regression: preset charset outline hashes match tests/golden/outline_hashes.json."""

from __future__ import annotations

import json
from pathlib import Path

from typekernel.parts import Controls, DesignContext
from typekernel.qa.outline_hash import composed_glyph_hash

_GOLDEN = Path(__file__).resolve().parents[1] / "golden" / "outline_hashes.json"

_PRESET_FACTORIES = {
    "humanist_sans": DesignContext.humanist_sans,
    "geometric_sans": DesignContext.geometric_sans,
    "code_clear": DesignContext.code_clear,
    "display": DesignContext.display,
    "open_print": DesignContext.open_print,
}


def _load_golden() -> dict[str, dict[str, str]]:
    data = json.loads(_GOLDEN.read_text(encoding="utf-8"))
    presets = data["presets"]
    assert isinstance(presets, dict)
    return presets


def test_outline_hashes_match_golden() -> None:
    golden = _load_golden()
    assert set(golden) == set(_PRESET_FACTORIES)
    for preset_name, factory in _PRESET_FACTORIES.items():
        controls = Controls.from_context(factory())
        glyphs = controls.build_all()
        expected = golden[preset_name]
        assert set(expected) == set(controls.supported)
        mismatches = [
            ch
            for ch in controls.supported
            if composed_glyph_hash(glyphs[ch]) != expected[ch]
        ]
        assert not mismatches, f"{preset_name}: hash drift on {mismatches!r}"

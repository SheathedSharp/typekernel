"""Verify or rewrite tests/golden/outline_hashes.json (TK-108)."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path

from typekernel.parts import Controls, DesignContext
from typekernel.qa.outline_hash import composed_glyph_hash

_ROOT = Path(__file__).resolve().parents[1]
_GOLDEN = _ROOT / "tests" / "golden" / "outline_hashes.json"

_PRESET_FACTORIES: dict[str, Callable[[], DesignContext]] = {
    "humanist_sans": DesignContext.humanist_sans,
    "geometric_sans": DesignContext.geometric_sans,
    "code_clear": DesignContext.code_clear,
    "display": DesignContext.display,
    "open_print": DesignContext.open_print,
    "slab_serif": DesignContext.slab_serif,
    "bracketed_serif": DesignContext.bracketed_serif,
}


def _build_golden() -> dict[str, dict[str, str]]:
    presets: dict[str, dict[str, str]] = {}
    for name, factory in _PRESET_FACTORIES.items():
        controls = Controls.from_context(factory())
        glyphs = controls.build_all()
        presets[name] = {
            ch: composed_glyph_hash(glyphs[ch]) for ch in controls.supported
        }
    return presets


def _load_file() -> dict[str, dict[str, str]]:
    data = json.loads(_GOLDEN.read_text(encoding="utf-8"))
    presets = data["presets"]
    if not isinstance(presets, dict):
        raise TypeError("golden root must have presets object")
    return presets


def _drift(
    expected: dict[str, dict[str, str]], actual: dict[str, dict[str, str]]
) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    if set(expected) != set(actual):
        raise SystemExit(f"preset keys differ: file={sorted(expected)} built={sorted(actual)}")
    for preset, exp in expected.items():
        got = actual[preset]
        if set(exp) != set(got):
            raise SystemExit(f"{preset}: charset keys differ")
        changed = [ch for ch in exp if exp[ch] != got[ch]]
        if changed:
            out[preset] = sorted(changed)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="rewrite tests/golden/outline_hashes.json from current HEAD outlines",
    )
    args = parser.parse_args(argv)
    built = _build_golden()
    if args.write:
        payload = {"presets": built}
        _GOLDEN.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(_GOLDEN)
        return 0
    drift = _drift(_load_file(), built)
    if not drift:
        return 0
    for preset, chars in sorted(drift.items()):
        print(f"{preset}: {', '.join(chars)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

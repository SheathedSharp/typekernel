"""Assemble auto + hand-written .fea; validate with feaLib (§11.2)."""

from __future__ import annotations

import io
import re
from pathlib import Path

from typekernel.features.generate import generate_features

__all__ = [
    "FeatureSyntaxError",
    "assemble_features",
    "load_hand_fea",
    "validate_fea",
]

_REPLACE = re.compile(r"^#\s*tk:replace\s+(\w+)\s*$", re.MULTILINE)


class FeatureSyntaxError(Exception):
    """feaLib rejected feature text; carries path/line when known."""

    def __init__(self, message: str, *, path: str | None = None, line: int | None = None):
        super().__init__(message)
        self.path = path
        self.line = line


def load_hand_fea(
    fea_dir: str | Path | None, *, root: str | Path | None = None
) -> tuple[str, set[str]]:
    """Load ``*.fea`` in name order. Returns ``(text, replaced_feature_tags)``."""
    if fea_dir is None:
        return "", set()
    path = Path(fea_dir)
    if not path.is_absolute():
        if root is None:
            return "", set()
        path = Path(root) / path
    if not path.is_dir():
        return "", set()
    parts: list[str] = []
    replaced: set[str] = set()
    for fea in sorted(path.glob("*.fea")):
        text = fea.read_text(encoding="utf-8")
        for m in _REPLACE.finditer(text):
            replaced.add(m.group(1))
        parts.append(f"# --- {fea.name} ---\n{text.rstrip()}\n")
    return "\n".join(parts), replaced


def _strip_auto_features(auto_text: str, replaced: set[str]) -> str:
    if not replaced:
        return auto_text
    out = auto_text
    for tag in replaced:
        out = re.sub(
            rf"feature\s+{re.escape(tag)}\s*\{{.*?\}}\s*{re.escape(tag)}\s*;\s*",
            "",
            out,
            flags=re.DOTALL,
        )
    return out


def assemble_features(
    glyph_names: set[str] | list[str],
    *,
    fea_dir: str | Path | None = "features",
    root: str | Path | None = None,
    extra: list[str] | tuple[str, ...] = (),
) -> str:
    """Auto features + hand .fea (with ``# tk:replace``) + extras."""
    auto = generate_features(set(glyph_names))
    hand, replaced = load_hand_fea(fea_dir, root=root)
    auto = _strip_auto_features(auto, replaced)
    chunks = [auto]
    if hand:
        chunks.append(hand)
    if extra:
        chunks.append("\n".join(extra))
    return "\n".join(c for c in chunks if c.strip()).rstrip() + "\n"


def validate_fea(text: str, *, path: str | None = None) -> None:
    """Parse with fontTools.feaLib; raise FeatureSyntaxError on failure."""
    try:
        from fontTools.feaLib.parser import Parser
    except ImportError as exc:  # pragma: no cover
        raise FeatureSyntaxError("fontTools.feaLib is required to validate features") from exc
    try:
        Parser(io.StringIO(text)).parse()
    except Exception as exc:
        line = getattr(exc, "line", None)
        raise FeatureSyntaxError(str(exc), path=path, line=line) from exc

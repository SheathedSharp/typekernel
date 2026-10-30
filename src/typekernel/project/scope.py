"""Charset scope helpers (S0 minimal charset)."""

from __future__ import annotations

from collections.abc import Iterable

from typekernel.project.evaluate import unicodes_for_glyph_name
from typekernel.project.session import ProjectSession

__all__ = ["glyph_in_scope", "scoped_glyph_names"]


def glyph_in_scope(session: ProjectSession, name: str) -> bool:
    """True when ``name`` is in scope for audit/proof under current charset mode."""
    project = session.project
    if project.charset is None or project.charset_mode != "minimal":
        return True
    charset = project.charset
    if name in charset.extra_names:
        return True
    spec = session.specs().get(name)
    if spec is None:
        # composites
        comp = project.composites.get(name)
        if comp is None:
            return False
        unicodes = list(comp.unicodes) if comp.unicodes is not None else list(
            unicodes_for_glyph_name(name)
        )
    else:
        unicodes = (
            list(spec.unicodes)
            if spec.unicodes is not None
            else list(unicodes_for_glyph_name(name))
        )
    if not unicodes:
        # no unicode — treat as out of minimal scope (placeholder)
        return False
    return any(cp in charset.codepoints for cp in unicodes)


def scoped_glyph_names(session: ProjectSession, names: Iterable[str] | None = None) -> list[str]:
    """Filter ``names`` (default: all specs) to charset-minimal scope."""
    base = list(names) if names is not None else sorted(session.specs())
    return [n for n in base if glyph_in_scope(session, n)]

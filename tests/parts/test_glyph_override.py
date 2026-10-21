"""Per-glyph derivation overrides on :class:`FormSources`."""

from __future__ import annotations

from typekernel.parts import DesignContext, FormSources, f_from_n


def test_with_glyph_replaces_derivation() -> None:
    ctx = DesignContext.code_clear()
    base = FormSources.from_context(ctx)
    wide_f = base.with_glyph("f", lambda n, o, c: f_from_n(n, c, arm=0.92))
    f0 = base.derive_one("f")
    f1 = wide_f.derive_one("f")
    assert f1.advance >= f0.advance

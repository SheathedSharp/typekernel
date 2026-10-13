"""Per-glyph derivation overrides on :class:`Controls`."""

from __future__ import annotations

from typekernel.parts import Controls, DesignContext, f_from_n


def test_with_glyph_replaces_derivation() -> None:
    ctx = DesignContext.code_clear()
    base = Controls.from_context(ctx)
    wide_f = base.with_glyph("f", lambda n, o, c: f_from_n(n, c, arm=0.92))
    f0 = base.build("f")
    f1 = wide_f.build("f")
    assert f1.advance >= f0.advance

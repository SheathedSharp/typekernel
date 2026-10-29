"""Project loading / build errors."""

from __future__ import annotations

__all__ = ["GlyphBuildError", "MigrationError"]


class GlyphBuildError(Exception):
    """Wrap a failure while evaluating or slot-filling a glyph.

    Attributes:
        glyph: Glyph name being built.
        master: Master name, or ``None`` for the default system.
        tag: Slot tag when the failure came from slot fill; else ``None``.
        cause: Original exception.
    """

    def __init__(
        self,
        glyph: str,
        master: str | None,
        cause: BaseException,
        *,
        tag: str | None = None,
    ) -> None:
        self.glyph = glyph
        self.master = master
        self.tag = tag
        self.cause = cause
        where = f"glyph {glyph!r}"
        if master is not None:
            where += f" master {master!r}"
        if tag is not None:
            where += f" slot {tag!r}"
        super().__init__(f"{where}: {cause}")


class MigrationError(Exception):
    """Project uses a removed convention; message lists old → new field map."""

    def __init__(self, message: str, *, mapping: dict[str, str] | None = None) -> None:
        self.mapping = dict(mapping or {})
        super().__init__(message)

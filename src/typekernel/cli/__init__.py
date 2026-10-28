"""CLI — ``tk new`` / ``tk build`` / ``tk proof`` (ARCHITECTURE.md「交接规格」)."""

from __future__ import annotations

__all__ = ["main"]


def main(argv: list[str] | None = None) -> int:
    from typekernel.cli.__main__ import main as _main

    return _main(argv)

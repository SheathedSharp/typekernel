"""Audit / check plugins (ARCHITECTURE.md checks family).

Built-ins: ``direction``, ``stem``, ``zone``, ``compat``, ``overlap``.
Projects append callables via ``EXTRA_CHECKS`` in ``system.py``::

    from typekernel.plugins.checks import stem as stem_check

    def pen_angle_hint(ctx):
        ...

    EXTRA_CHECKS = (pen_angle_hint,)
"""

from __future__ import annotations

from typekernel.plugins.checks import compat, direction, overlap, stem, zone
from typekernel.plugins.checks.protocol import CheckContext, CheckFn, Finding, raw_drawing

__all__ = [
    "CheckContext",
    "CheckFn",
    "Finding",
    "raw_drawing",
    "compat",
    "direction",
    "overlap",
    "stem",
    "zone",
    "DEFAULT_CHECKS",
    "builtin_checks",
]


def builtin_checks(
    *,
    check_stem: bool = True,
    check_zone: bool = True,
    check_direction: bool = True,
    check_compat: bool = True,
    check_overlap: bool = False,
) -> tuple:
    """Return the default check callables for ``tk audit`` flags."""
    out = []
    if check_direction:
        out.append(direction.check)
    if check_stem:
        out.append(stem.check)
    if check_zone:
        out.append(zone.check)
    if check_overlap:
        out.append(overlap.check)
    if check_compat:
        out.append(compat.check)
    return tuple(out)


DEFAULT_CHECKS = builtin_checks()

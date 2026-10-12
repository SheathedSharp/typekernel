"""Explicit join-cleanup operators.

Join cleanup is a named optical policy, never a silent ``simplify(tol)`` that
destroys extrema and handle intent.
"""

from __future__ import annotations

from typing import Literal

from typekernel.geo.outline import Outline

JoinPolicy = Literal["noop", "tangent_fix", "ink_trap"]


def cleanup_joins(outline: Outline, policy: JoinPolicy = "noop") -> Outline:
    """Apply an explicit join-cleanup policy; return a (possibly new) outline.

    Policies:

    - ``noop`` (default): return the same outline object unchanged. No geometry
      is rewritten, so handles and extrema stay intact.
    - ``tangent_fix``: reserved — raise ``NotImplementedError``.
    - ``ink_trap``: reserved — raise ``NotImplementedError``.

    Calling ``simplify`` (or any tolerance-based path reduction) under any
    policy name is forbidden here.
    """
    if policy == "noop":
        return outline
    if policy in ("tangent_fix", "ink_trap"):
        raise NotImplementedError(
            f"cleanup_joins policy {policy!r} is reserved and not implemented"
        )
    raise ValueError(f"unknown join cleanup policy: {policy!r}")

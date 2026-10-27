"""Errors raised by the draw kernel."""

from __future__ import annotations


class ContinuityError(ValueError):
    """Raised when a join that must be G1 is not.

    The message should include a node tag or coordinates and the measured error
    so writers can fix the fragment instead of post-hoc sealing.
    """

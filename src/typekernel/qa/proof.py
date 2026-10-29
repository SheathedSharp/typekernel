"""Compatibility shim — proofs live in :mod:`typekernel.perceive.specimen`."""

from __future__ import annotations

from typekernel.perceive import specimen as _specimen
from typekernel.perceive.specimen import *

__all__ = list(_specimen.__all__)

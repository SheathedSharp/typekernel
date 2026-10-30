"""Pure letter-topology priors (S2) — data, not constructors.

Architecture exception (ARCHITECTURE 架构守卫): glyph / letter **names** may
appear in this package only. Kernel constructors, anatomy builders, and
diagnose checks must still address shapes by Unicode / topology, never by
hard-coded letter builders.
"""

from __future__ import annotations

from typekernel.knowledge.confuse import CONFUSE_PAIRS, confuse_partners
from typekernel.knowledge.priors import (
    LATIN_BASIC,
    TopologyPrior,
    prior_for,
    priors_for_text,
)

__all__ = [
    "CONFUSE_PAIRS",
    "LATIN_BASIC",
    "TopologyPrior",
    "confuse_partners",
    "prior_for",
    "priors_for_text",
]

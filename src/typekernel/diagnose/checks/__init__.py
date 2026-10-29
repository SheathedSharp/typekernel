"""Built-in diagnose checks (letter-agnostic; driven by expect / traits / tags)."""

from __future__ import annotations

from typekernel.diagnose.checks.anchors import AnchorsCheck
from typekernel.diagnose.checks.features import FeaturesSyntaxCheck
from typekernel.diagnose.checks.gray import GrayCheck
from typekernel.diagnose.checks.tags import TagsGrammarCheck
from typekernel.diagnose.checks.spacing import (
    PairCollisionCheck,
    RefConsistencyCheck,
    SpacingCheck,
)
from typekernel.diagnose.checks.topology import TopologyCheck
from typekernel.diagnose.checks.vertical import VerticalCheck

__all__ = [
    "AnchorsCheck",
    "FeaturesSyntaxCheck",
    "GrayCheck",
    "TagsGrammarCheck",
    "PairCollisionCheck",
    "RefConsistencyCheck",
    "SpacingCheck",
    "TopologyCheck",
    "VerticalCheck",
]

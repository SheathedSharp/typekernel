"""QA helpers: outline hashes, PNG specimens, approval gates, proofs.

Frozen parts-era score / lint / sentence_gate modules were removed.
"""

from __future__ import annotations

from typekernel.qa.gates import load_approval, require_approval, write_approval
from typekernel.qa.outline_hash import glyph_hash, outline_hash
from typekernel.qa.proof import (
    DEFAULT_KERN_PAIRS,
    DEFAULT_SPACING_STRINGS,
    proof_axis_ladder,
    proof_charset_grid,
    proof_context,
    proof_kern_pairs,
    proof_labeled_waterfall,
    proof_sheet,
    proof_spacing_strings,
    proof_weight_ladder,
)

__all__ = [
    "DEFAULT_KERN_PAIRS",
    "DEFAULT_SPACING_STRINGS",
    "glyph_hash",
    "load_approval",
    "outline_hash",
    "proof_axis_ladder",
    "proof_charset_grid",
    "proof_context",
    "proof_kern_pairs",
    "proof_labeled_waterfall",
    "proof_sheet",
    "proof_spacing_strings",
    "proof_weight_ladder",
    "require_approval",
    "write_approval",
]

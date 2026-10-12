"""QA helpers for typekernel: outline hashes, PNG specimens, human-gate records.

This package supports regression checks and human visual review. A PNG specimen
is a **preview only** — cubic outlines remain the design truth. Approval helpers
never auto-approve a gate; a human must write the JSON record.
"""

from __future__ import annotations

from typekernel.qa.gates import load_approval, require_approval, write_approval
from typekernel.qa.outline_hash import outline_hash

__all__ = [
    "load_approval",
    "outline_hash",
    "require_approval",
    "write_approval",
]

# ``render_outline_png`` lives in ``specimen_png`` and needs the optional
# ``specimen`` extra (Pillow). Import it from there when rendering.

"""QA helpers for typekernel: outline hashes, PNG specimens, scores, gates.

This package supports regression checks and human visual review. A PNG specimen
is a **preview only** — cubic outlines remain the design truth. Approval helpers
never auto-approve a gate; a human must write the JSON record.
"""

from __future__ import annotations

from typekernel.qa.agent_preview import (
    DEFAULT_FOCUS_GLYPHS,
    build_glyph_preview,
    charset_for_preview,
)
from typekernel.qa.design_review import (
    WEAK_GLYPHS,
    DesignReview,
    design_review,
)
from typekernel.qa.gates import load_approval, require_approval, write_approval
from typekernel.qa.outline_hash import outline_hash
from typekernel.qa.score import (
    Score,
    WordReport,
    join_smoothness,
    stem_uniformity,
    word_gap_spread,
    word_report,
    zayju_report,
)
from typekernel.qa.sentence_gate import (
    AGENT_PAIRS,
    AGENT_SENTENCE,
    SentenceGateLimits,
    check_sentence_gate,
    controls_pair_gaps,
    controls_sentence_report,
)
from typekernel.qa.style_consistency import (
    GlyphStyleMetrics,
    SequenceStyleReport,
    StyleCheck,
    StyleConsistencyReport,
    StyleConsistencyTolerances,
    check_design_sequence,
    compare_glyph_styles,
    extract_glyph_style_metrics,
    fix_hint_for_check,
    script_body_tolerances,
    script_sequence_tolerances,
    script_topology_skip_checks,
)

__all__ = [
    "AGENT_PAIRS",
    "AGENT_SENTENCE",
    "DEFAULT_FOCUS_GLYPHS",
    "WEAK_GLYPHS",
    "DesignReview",
    "GlyphStyleMetrics",
    "Score",
    "SentenceGateLimits",
    "SequenceStyleReport",
    "StyleCheck",
    "StyleConsistencyReport",
    "StyleConsistencyTolerances",
    "WordReport",
    "build_glyph_preview",
    "charset_for_preview",
    "check_design_sequence",
    "check_sentence_gate",
    "compare_glyph_styles",
    "controls_pair_gaps",
    "controls_sentence_report",
    "design_review",
    "extract_glyph_style_metrics",
    "fix_hint_for_check",
    "join_smoothness",
    "load_approval",
    "outline_hash",
    "require_approval",
    "script_body_tolerances",
    "script_sequence_tolerances",
    "script_topology_skip_checks",
    "stem_uniformity",
    "word_gap_spread",
    "word_report",
    "write_approval",
    "zayju_report",
]

# ``render_outline_png`` lives in ``specimen_png`` and needs the optional
# ``specimen`` extra (Pillow). Import it from there when rendering.

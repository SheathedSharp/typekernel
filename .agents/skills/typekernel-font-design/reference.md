# typekernel — module map (agent reference)

## Layers

```
DesignContext     family proportions (stem, x-height, contrast, terminals, …)
       ↓
Controls          n/o/H/O metrics + build_all() → dict[str, ComposedGlyph]
       ↓
space_font        optical sidebearings
       ↓
Font              cmap, metrics, groups, kerning, features.fea text
       ↓
build_font        UFO → OTF/TTF/WOFF2
build_variable_font   masters → designspace → VF
polish_glyph_map      join cleanup after build_all (default in compose_font)
```

## Key imports

```python
from typekernel.parts import Controls, DesignContext, auto_class_kern, auto_side_kern_classes, rhythm_from_control_glyphs
from typekernel.parts.italic import italic_design
from typekernel.optics.space import space_font
from typekernel.font import Font, Master
from typekernel.compile import build_font, build_variable_font
from typekernel.compile.features import (
    add_case_punctuation,
    add_standard_ligatures,
    add_tabular_alternates,
    standard_feature_text,
)
from typekernel.compile.oblique import oblique_font  # slnt only, not ital semantics
from typekernel.qa.proof import proof_context, proof_sheet, proof_labeled_waterfall
from typekernel.qa.design_review import design_review
from typekernel.qa.family_gate import check_family_gate, collect_family_gate_failures
from typekernel.qa.trial_protocol import snapshot_trial, FIXED_TRIAL_BRIEFS
```

`design_review(...).charset_failures` runs lint + identity on `controls.supported` (same as family gate). Agent builds should exit non-zero when non-empty.

## Glyph specs (`tuned_glyph`)

Typed knobs in `parts/glyph_specs.py` (defaults match stock derivations):

| Char | Spec | Fields |
| --- | --- | --- |
| `f` `t` `j` `a` `s` `e` | `FSpec` … `SSpec` | see dataclass docstrings |
| `A` `G` `K` `R` `Y` `V` `W` `X` `M` `N` | cap specs | `CapASpec` `width`/`apex`/`bar`; `bar_reach`; `width`/`vertex`; `leg_at`/…; `junction`; `apex` (M) |

L0 still requires ≥2 overrides among `f t j a s e`; cap specs are for family polish and review notes.

## Glyph derivation (today)

- Lowercase: mostly `n` / `o` families (`RELATED_FORMS` in `parts/family.py`).
- Uppercase & default figures: `H` / `O`.
- Punctuation: `PUNCT_FORMS` (includes `$` `%` `@`).
- Ligatures: `fi`, `fl` via `parts/ligatures.py` + `add_standard_ligatures`.

Derived `f`, `t` use hook body + **rounded crossbar union** (needs `typekernel[boolean]` / pathops; else notch fallback). Sentence proof mandatory.

## Master compatibility (`check_masters`)

Fails if:

- Axis constant across all masters (each VF axis needs min ≠ max).
- Glyph set or order differs between masters.
- Kerning **groups** differ (kern *values* may differ).
- Outlines not interpolatable (point count / structure).

## Common failures

| Error | Fix |
| --- | --- |
| Feature references missing `.tf` / `.case` | Add alternates or `standard_feature_text(tnum=False, case=False)` |
| `wght does not vary` | Add master at another weight |
| `kerning groups differ` | Share `auto_side_kern_classes` from reference master |
| Ugly style despite tuning | Wrong topology for brief—extend `parts`, do not only tune context |

## Tests

After library changes: `uv run pytest -q`. Compile tests need `ufo2ft` (`[compile]` extra).

## Approvals

Human-reviewed areas: `approvals/*.json`. Respect listed constraints when changing compile or optics behavior.

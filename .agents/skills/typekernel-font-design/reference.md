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
from typekernel.parts.italic import italic_design, vf_italic_pair, vf_upright_controls
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
| caps A–Z (not `H`/`I`) | see `glyph_specs` | bowl + `O`：`B`/`D`/`P`/`R`/`U`/`J`; ring：`C`/`G`/`S`/`Q`; 其余见 `agent-recipes` 表 |

L0 still requires ≥2 overrides among `f t j a s e`; cap specs are for family polish and review notes.

## Style DNA (`parts/style.py`)

`Controls.from_context(ctx, style=Style(...))` or `controls.with_style(...)`. Defaults match pre-305 presets (golden hashes unchanged).

| Field | Default | Non-default | Main effect |
| --- | --- | --- | --- |
| `a_form` | `single` | `double` | two-storey `a` |
| `g_form` | `single` | `double` | two-storey `g` |
| `l_tail` | `none` | `tailed` | `l` tail hook |
| `y_tail` | `straight` | `curved` | `y` lower-right curve |
| `i_dot` | `round` | `square` / `diamond` | `i` `j` dot |
| `t_cut` | `flat` | `slanted` | `t` foot (independent of `terminal_style`) |
| `serif` | `none` | `slab` / `bracketed` | stem serifs; presets `slab_serif()` / `bracketed_serif()` |

VF notes: `g_form=double` / `a_form=double` need `check_masters` on weight ladders (see `tests/parts/test_style_gate.py`). Serif voices need sentence gate + L3 distance tests.

## Contrast & stress (TK-301 / TK-302)

- **`contrast`**: round stroke horizontal ÷ vertical thickness (`bowl`, `o`, figures). Knob reach: `test_contrast_moves_round_letters`.
- **`stress`**: degrees CCW rotation of the thin point on round counters (`0` = default presets / golden hashes). Affects `o` `c` `s`, cap `S`, lining `2` `3` `5` `6` `8` `9`. Regression: `tests/parts/test_stress.py`; agent notes: [agent-recipes.md](../../../docs/agent-recipes.md) §对比度与应力.

## Construction spike — skeleton + pen (TK-308)

Not a weight axis. Optional `parts.skeleton.trace_letter` + `geo.stroke` contrast pen for experiments or hand-traced strokes before `with_glyph`.

| API | Role |
| --- | --- |
| `Stroke.from_points` | Polyline midline; with `offset_fit_budget>0`, `polyline_to_cubic_centerline` then `expand_cubic` |
| `Stroke.from_beziers` | Cubic midline → `expand_cubic` |
| `Skeleton.from_mapping` | Plan dict; stroke dict may include `beziers`, `chord_budget`, `offset_fit_budget`, `join`, `cap` |
| `cubic_centerline_to_polyline` | Chord-budget flatten → chain to `expand` (open multi-segment path) |
| `trace_letter` | Expand skeleton; default `heal` / `strip_tiny` / `refit_cubics` after union (see `examples/zayju_script/`) |
| `expand_cubic` | `(Outline, CenterlineExpandReport)`; open path uses offset-rail cubics when `offset_fit_budget>0` (butt/round/square cap; miter/round/bevel join). Set `offset_fit_budget=0` to flatten midline + `expand`. |

Do not use for L0–L2 preset trials unless the brief explicitly needs new stroke topology. See `docs/agent-recipes.md` §骨架构造 spike. Program acceptance: `tests/parts/test_stroke_program_acceptance.py`, `tests/examples/test_zayju_script.py`.

## Italic & oblique (M4)

- **Italic master**: `italic_design(regular)` — construct slant via `italic_slant_deg`, branching `n/h/r/u/m`, `f` descender. For `wght×ital` VF prefer `vf_italic_pair(regular, style=ItalicStyle(...))` (matched oblique pre-split angle) or `vf_upright_controls(regular, oblique_split_deg=…)` + `italic_design(upright, …)`.
- **Oblique**: `oblique_font` / `ObliqueTransform` — mechanical shear only; do not label as Italic.
- **TK-402**: `parts/oblique_compat.py` pre-splits before slant for glyphs outside `OBLIQUE_COMPAT_EXCLUDE` (`e` bakes splits in `e_from_o` via `outline_e_oblique_splits`). `OBLIQUE_PRE_EXTREMA` (`mu`). VF upright uses branching arches when `vf_compat_oblique_splits`.

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

## Agent trials (M5 / TK-502)

- Baselines: `examples/agent_trial/snapshot_presets.py`, `snapshot_serif_voices.py`.
- Reference edits (L3 + gate/R8): `design_warm_humanist.py`, `design_editorial_geometric.py`, `design_editorial_slab.py` / `design_editorial_bracketed.py` (brief-2 `--variant slab|bracketed`), `design_coding_clear.py` — each exports `controls()`, `design_bold()`, `baseline_controls()`.
- Metrics JSON: `snapshot_design.py --brief … --design …` or `snapshot_reference_trials.py` (includes `brief-2-slab/`). Both run `validate_trial_snapshot` then exit via `trial_snapshot_exit_code` (0 ok; 2 metrics; 3 gate; 4 R8 ladder; 5 inconsistent JSON fields; 6 not L3; 7 `cheating_flags` e.g. stem-only scale). Audit saved JSON: `validate_snapshot.py path/to/snapshot.json` or `validate_snapshot.py --recursive artifacts/trials/<run>/`; after human scores are in JSON, `validate_snapshot.py --require-human-scores` (exit 8 if incomplete). Program snapshots from `snapshot_design.py` must not include `human_review_scores` until a human adds them.
- `snapshot_trial` → `weight_ladder_r8_failures` uses full trial `Controls` on `WEIGHT_LADDER_STEMS` (30–200) via `controls_at_ladder_stem`.
- Regular + Bold OTF + proof: `build_reference_family.py --brief brief-{1,2,3} [--variant slab] --out …` (`AGENT_SENTENCE` absolute gate; L3 voices skip preset-relative `design_review` failures). End-to-end checklist: `docs/AGENT_TRIALS.md` §终验流程.
- Human review PNG bundle (no `approvals/` writes): `examples/human_review_bundle.py` (serif VF proofs + italic `proof.png` / `proof_vf.png`; `--only appendix-b` → `appendix_b_three_g_humanist.png` + `appendix_b_s_opening_humanist.png` for appendix B-13–B-15).
- TK-207 weight ladder (local `artifacts/specimens/`): `examples/weight_ladder_sheet.py --preset humanist_sans --out …`.
- TK-104 charset review (width ≤ 1600px): `examples/contact_sheet.py --preset … --out …`; voice diff: `examples/diff_overlay.py --trial-preset … --baseline-preset …` (same as `design_review` `contact.png` / `diff_overlay.png` under `out/review/`).
- TK-108 outline golden: `examples/regenerate_outline_hashes.py` (check drift; `--write` updates `tests/golden/outline_hashes.json` after intentional outline edits).
- Program acceptance (before human `approvals/`): `PYTHONPATH=src python examples/run_program_exit.py` (`--gate slab|bracketed|italic|all`, `--with-linters`); or `pytest -q tests/parts/test_serifs.py::test_serif_voice_meets_program_acceptance`, `tests/parts/test_italic_program_acceptance.py`, `tests/docs/test_development_plan_section8.py`.

## Tests

After library changes: `uv run pytest -q`. Compile tests need `ufo2ft` (`[compile]` extra). Program exit: `examples/run_program_exit.py` or `pytest -q tests/docs/test_development_plan_section8.py`.

## Approvals

Human-reviewed areas: `approvals/*.json`. Respect listed constraints when changing compile or optics behavior.

## Sequential style consistency

For any face (Controls or skeleton), after each new glyph:

```python
from typekernel.qa import compare_glyph_styles, check_design_sequence

report = compare_glyph_styles(control_glyph, candidate, reference_name="a", candidate_name="e")
assert report.passed, report.failures
```


## Designer-order (`DesignSequence`)

```python
from typekernel.qa import DesignSequence
from typekernel.parts import Controls, DesignContext

controls = Controls.from_context(DesignContext.geometric_sans())
seq = controls.design_sequence(order=("n", "o", "h"), control="n")
seq.add("o", controls.build("o"))
seq.add("h", controls.build("h"))
glyphs = seq.export_glyphs(require_complete=True)
```

On refuse, `DesignSequenceError.hints` / `seq.hints_from_last()` name the
metric and the redesign direction. Phrase / `BRIEF_SENTENCE` proofs come
**after** export. See `examples/zayju_script/design.py` (`build_charset_sequential`
wraps `DesignSequence`; ungated `build_charset` is deprecated).


# Agent trial helpers (TK-502)

| Script | Role |
| --- | --- |
| `snapshot_presets.py` | Unmodified preset baselines (voice distance ≈ 0). |
| `snapshot_serif_voices.py` | `slab_serif` / `bracketed_serif` L3 baselines. |
| `design_warm_humanist.py` | brief-1 edited sheet (L3 + gate/R8). |
| `design_editorial_geometric.py` | brief-2 edited sheet (geometric sans). |
| `design_editorial_slab.py` | brief-2 slab serif variant (`--variant slab`). |
| `design_editorial_bracketed.py` | brief-2 bracketed serif variant (`--variant bracketed`). |
| `design_coding_clear.py` | brief-3 edited sheet. |
| `snapshot_design.py` | Run `snapshot_trial` on any module that exports `controls()`. |
| `snapshot_reference_trials.py` | All three `design_*.py` → `out/brief-*/snapshot.json`. |
| `build_reference_family.py` | `--brief brief-{1,2,3}` → Regular + Bold OTFs + `proof.png`. |
| `build_brief1_reference.py` | Thin wrapper for brief-1 only. |

```bash
# Reference trial (metrics gate; raise voice_distance toward L3 in the design file)
PYTHONPATH=src python examples/agent_trial/snapshot_design.py \
  --brief brief-1 --out artifacts/trials/warm-humanist-ref

# All reference briefs
PYTHONPATH=src python examples/agent_trial/snapshot_reference_trials.py \
  --out artifacts/trials/reference-designs
```

CI: `tests/examples/test_agent_trial_reference.py`, `tests/qa/test_m3_exit.py` (M3 L3 voice triad), `tests/qa/test_trial_protocol.py` (`test_serif_voice_trial_snapshots_meet_l3`).

Serif/italic **visual** review (separate from trial snapshots): `examples/human_review_bundle.py` → `approvals/serif-*-voice.json`, `italic-vf-construct.json`.

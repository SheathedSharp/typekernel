# Agent trial helpers (TK-502)

| Script | Role |
| --- | --- |
| `snapshot_presets.py` | Unmodified preset baselines (voice distance ≈ 0). |
| `snapshot_serif_voices.py` | `slab_serif` / `bracketed_serif` L3 baselines. |
| `design_warm_humanist.py` | brief-1 edited sheet (L3 + gate/R8). |
| `design_editorial_geometric.py` | brief-2 edited sheet. |
| `design_coding_clear.py` | brief-3 edited sheet. |
| `snapshot_design.py` | Run `snapshot_trial` on any module that exports `controls()`. |

```bash
# Reference trial (metrics gate; raise voice_distance toward L3 in the design file)
PYTHONPATH=src python examples/agent_trial/snapshot_design.py \
  --brief brief-1 --out artifacts/trials/warm-humanist-ref
```

CI: `tests/examples/test_agent_trial_reference.py`.

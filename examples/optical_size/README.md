# Example: text + display masters → ``opsz`` variable font

Optical size is a **designed** delta, not a scale. Text (`opsz=14`) uses a
slightly heavier stem, opener aperture, and tighter tracking; display
(`opsz=72`) goes lighter, looser, and more overshoot via
`context_for_opsz`.

```bash
pip install -e ".[dev,specimen,compile,boolean]"
python examples/optical_size/build_opsz_vf.py
```

Outputs land in `out/` (gitignored except when you choose to keep proofs):

| File | Notes |
| --- | --- |
| `*-VF.ttf` | Variable font with `opsz` 14–72 |
| `proof_vf.png` | Ladder at opsz 14 / 28 / 42 / 56 / 72 |
| `proof.png` | Static Text vs Display waterfall |
| `static/` | OTF snapshots of each master |

## APIs

- `typekernel.parts.context_for_opsz` — text↔display `DesignContext` deltas
- `typekernel.font.Master` + `build_variable_font` — same path as `wght` / `ital` examples
- `typekernel.qa.proof.proof_axis_ladder` — instance ladder on axis 0 (`opsz` here)

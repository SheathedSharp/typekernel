# Anti-patterns

| Don’t | Do instead |
| --- | --- |
| Hunting for a letter builder inside `typekernel.*` | Use `System` + project glyphs (`tk new --starter latin-sans`) |
| Add heal / blend / seal after boolean mess | Change the fragment / overlap construction |
| Call `self_union` / boolean to hide a bad join in glyph code | Fix the fragment; use `tk build --resolve-overlaps` only for static ship |
| `tk build --resolve-overlaps` with `--variable` | Keep VF masters overlapping; resolve static instances only |
| Stroke-expand to fake weight | Scale `system.stem` (and masters via `tuned`) |
| Letter builders inside `typekernel.*` kernel packages | Keep letters in the project starter only |
| Bbox-only advances forever | `spacing.py` metrics keys + `apply_spacing` |
| Silent mega-knobs (`aperture`, `roundness`) | Explicit tokens + element functions |
| Treating `tk audit` warnings as pass/fail cosmetics gate | Treat direction/compat as hard fail; stem/zone as fix list |
| Ignoring `--overlap` cavities then shipping even-odd proofs | Inspect with `tk proof --glyph`; fix fragments or accept VF overlap + nonzero ship fill |
| Reimplementing `hook` / `tensioned_arc` / oriented stem math | Use `draw.construct` + `optics.stem` (see reference.md) |
| Inventing a letter-specific API to put in the kernel | Follow the ARCHITECTURE.md 标准工作流 |
| Writing private PIL phrase/crop scripts for proofs | `tk proof --text` / `--glyph` / `ladder` |

# Anti-patterns

| Don’t | Do instead |
| --- | --- |
| Hunting for a letter builder inside `typekernel.*` | Use `System` + project glyphs (`tk new --starter latin-sans`) |
| Add heal / blend / seal after boolean mess | Change the fragment / overlap construction |
| Stroke-expand to fake weight | Scale `system.stem` (and masters via `tuned`) |
| Bbox-only advances forever | `spacing.py` metrics keys + `apply_spacing` |
| Silent mega-knobs (`aperture`, `roundness`) | Explicit tokens + element functions |
| Treating `tk audit` warnings as pass/fail cosmetics gate | Treat direction/compat as hard fail; stem/zone as fix list |
| Inventing a letter-specific API to put in the kernel | Follow the ARCHITECTURE.md 标准工作流 |

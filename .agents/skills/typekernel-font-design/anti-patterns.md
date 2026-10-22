# Anti-patterns

## Stroke-expand “weight”

Using `Pen.expand` / `expand_polyline` / outline inflate to fake Bold.

**Why wrong:** sticky joins, dead counters, not a designed master.  
**Do instead:** new context + recompose yokes/builders (`stem`, counters, relief).

## Shear-as-italic

`oblique_font`, lean/tracking tricks, or a single matrix shear labeled Italic.

**Why wrong:** upright topology stays upright; branching letters look wrong.  
**Do instead:** yoke `branch_y` / builders on italic context / `italic_design`;
proof against upright. Do not flip italic-VF construct flags by hand.

## Kit-of-parts when a yoke exists

Building `n`/`h`/`m`/`u`/`r`/`a`/`c`/`e`/`s` (and bowl+stem `b`/`d`/`p`/`q`) from
`vertical_stem` + `shoulder`/`arch`/`u_bowl` + boolean union while a public yoke
already draws that body continuously.

**Why wrong:** segment recipes drift from builders/VF, extra boolean debt, fights
the locked Usage A continuous path.  
**Do instead:** `n_yoke` / `h_yoke` / `double_shoulder_yoke` / `u_yoke` / `r_yoke` /
`bowl_stem_yoke` / `a_yoke` / `c_yoke` / `e_yoke` / `s_yoke`, or letter builders
that prefer them. Use `soft_union` only for shapes yokes do not cover yet.

## Dead knobs

Tweaking floats that do not change the glyphs you ship (e.g. unused `aperture`
when you never call opening yokes; huge `tracking` instead of sidebearings;
`vf_compat_stem_segments` on a one-off static Regular with no ital axis).

**Do instead:** change a field, recompose, prove the outline/metrics moved
(`test_knob_coverage` mindset).

## Aggregate factory as design

Deleted `Controls.build_all`, ungated charset dumps, `DesignSequence` / `unlock_*`
as the *only* legal path, or copying `examples/_legacy/agent_*` as the product.
**Do not resurrect Controls.**

**Do instead:** Usage A — compose parts/yokes in your own script.

## Phrase-batch design

Defining a specimen sentence and generating every letter only to satisfy a gate,
without inspecting controls.

**Do instead:** design letters you care about (≥2 recipes for the brief); specimen last.

## Features without glyphs

Emitting `liga` / `case` / `frac` that reference names you never added.

**Do instead:** add glyphs first; enable features to match.

## Skeleton as weight axis

`trace_letter` / centerline expand as a `wght` master chain.

**Do instead:** keep skeleton for script spikes; weight stays designed deltas.

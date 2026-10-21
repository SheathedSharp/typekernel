# Anti-patterns

## Stroke-expand “weight”

Using `Pen.expand` / `expand_polyline` / outline inflate to fake Bold.

**Why wrong:** sticky joins, dead counters, not a designed master.  
**Do instead:** new context + recompose (`stem`, counters, relief).

## Shear-as-italic

`oblique_font`, lean/tracking tricks, or a single matrix shear labeled Italic.

**Why wrong:** upright topology stays upright; branching letters look wrong.  
**Do instead:** `italic_design` / rewritten italic parts; proof against upright.

## Dead knobs

Tweaking floats that do not change the glyphs you ship (e.g. unused `aperture` when you never call open-bowl builders; huge `tracking` instead of sidebearings).

**Do instead:** change a field, recompose, prove the outline/metrics moved (`test_knob_coverage` mindset).

## Aggregate factory as design

deleted `Controls.build_all`, ungated charset dumps, `DesignSequence` / `unlock_*` as the *only* legal path, or copying `examples/_legacy/agent_*` as the product.

**Do instead:** Usage A — compose parts in your own script.

## Phrase-batch design

Defining a specimen sentence and generating every letter only to satisfy a gate, without inspecting controls.

**Do instead:** design letters you care about; specimen comes last.

## Features without glyphs

Emitting `liga` / `case` / `frac` text that references names you never added.

**Do instead:** add glyphs first; enable features to match.

## Skeleton as weight axis

`trace_letter` / centerline expand as a `wght` master chain.

**Do instead:** keep skeleton for script spikes; weight stays designed deltas.

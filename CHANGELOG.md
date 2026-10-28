# Changelog

Notable changes to typekernel. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project has not
cut a versioned release yet, so everything below is unreleased.

## [Unreleased]

### Changed

- `docs/ARCHITECTURE.md` now describes the architecture as it is — three-layer
  separation, core concepts, standard workflow, acceptance, package layout,
  handover contracts, architecture guards, test list, and design boundaries.
  The migration narrative that argued about removing `typekernel.parts` moved
  out of the repository.
- `ruff` is version-pinned in the `dev` extra. The lint gate is ruff's curated
  default rule set, which grows between releases; previously an unpinned
  `ruff>=0.6` let a new release change what CI enforced without any commit here.
- Starter templates (`typekernel.starters.*`) are exempt from `strict` mypy.
  They are project code that `tk new` copies into a user's font project, so
  holding them to kernel typing rules was never right.

### Removed

- Approval records for gates whose subjects no longer exist, plus 20 unreferenced
  historical images under `docs/images/`.
- Dead ignore rules for example directories that were deleted, and
  `tests/golden/outline_hashes.json`, which nothing read.

### Fixed

- CI passes for the first time. `ruff check src tests` and `mypy -p typekernel`
  were both failing on every commit since the workflow was added.
- `compile.oblique_font` was exported but could not run: it built its result with
  `Font(context=…)`, and `Font` has no `context` field. It now carries `system`
  across, and `tests/compile/test_oblique.py` covers it.
- A corner fill with trim distances but no replacement path raised
  `AttributeError` instead of trimming. `draw.slots` now treats that as a
  trim-only fill, which is what the fill protocol already implied.
- `approvals/compile-bridge.json` and `approvals/font-model.json` used
  `approved_by` / `approved_at` / `evidence`, which `load_approval` rejects.
  They now use the documented fields. `tests/qa/test_gates.py` guards every
  record in `approvals/` so this cannot rot again.

### Added

- `CONTRIBUTING.md`, `CHANGELOG.md`, and a documentation index in the README.

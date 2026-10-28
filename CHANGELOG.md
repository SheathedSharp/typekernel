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

### Removed

- Approval records for gates whose subjects no longer exist, plus 20 unreferenced
  historical images under `docs/images/`.
- Dead ignore rules for example directories that were deleted, and
  `tests/golden/outline_hashes.json`, which nothing read.

### Fixed

- `approvals/compile-bridge.json` and `approvals/font-model.json` used
  `approved_by` / `approved_at` / `evidence`, which `load_approval` rejects.
  They now use the documented fields. `tests/qa/test_gates.py` guards every
  record in `approvals/` so this cannot rot again.

### Added

- `CONTRIBUTING.md`, `CHANGELOG.md`, and a documentation index in the README.

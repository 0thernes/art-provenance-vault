# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-11

### Added

- Repository scaffold: README, LICENSE (MIT), contributing and security policies.
- `docs/ARCHITECTURE.md`: six-layer design — content hashing, signed manifests,
  git tamper-evidence chain, C2PA alignment, four-stage watermark pipeline,
  storage and anchoring strategy.
- `docs/ROADMAP.md`: PoC → MVP → v1 phases with acceptance criteria.
- `docs/LEGAL-NOTES.md`: licensing-landscape research notes (SPDX, CC,
  commercial terms, AI-art copyright open questions).
- `docs/adr/0001-record-architecture-decisions.md`: ADR process adopted.
- `schemas/manifest.schema.json`: JSON Schema (draft 2020-12) for the artwork
  manifest — creator, sha256, SPDX license, parent works, watermark records,
  chain-prev linkage.
- `src/provenance.py`: stdlib-only PoC CLI with `register` and `verify`
  commands implementing the hash → manifest → git commit loop.
- CI workflow: Python compile/lint check plus manifest schema validation.

[Unreleased]: https://example.invalid/compare/v0.1.0...HEAD
[0.1.0]: https://example.invalid/releases/tag/v0.1.0

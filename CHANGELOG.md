# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-06-11

### Added

- `docs/IP-STRATEGY.md`: five-pillar IP-protection strategy — invisible/robust
  watermark fallback, blockchain public ledger anchoring, extensive per-file
  metadata, human-authorship layering (2-of-3 human-majority design), and
  public-repo durable storage. Includes a "Legal reality check" section
  accurately summarizing *Thaler v. Perlmutter* (D.D.C. 2023, affirmed D.C.
  Cir. March 2025) and current US Copyright Office human-authorship guidance,
  with an explicit not-legal-advice disclaimer.

### Changed

- `schemas/manifest.schema.json`: added `human_attestations[]` array (layer,
  actor, action, timestamp, signature placeholder), `ai_generation` object
  (model, prompt-ref, params), and `ledger_anchor` object (chain,
  tx_or_merkle_ref, merkle_root, anchored_at). Schema remains valid JSON
  Schema 2020-12; `watermarks[]` array preserved unchanged.
- `docs/ARCHITECTURE.md`: added IP-STRATEGY.md cross-reference header, updated
  Layer 2 manifest field table to include the three new objects, and expanded
  the human-contribution design note to describe the 2-of-3 attestation model.
- `README.md`: added Five-Pillar IP-Protection Strategy section with table and
  cross-link to IP-STRATEGY.md; added IP-STRATEGY.md to Quality & Audit docs
  index.
- `docs/LEGAL-NOTES.md`: added IP-STRATEGY.md cross-reference to disclaimer
  block and section 5; expanded section 5 with the *Thaler* case summary and
  link to IP-STRATEGY.md Pillar 4.

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

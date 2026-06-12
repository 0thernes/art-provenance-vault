# T-003 — Local content-addressed asset store (`vault/assets/`)

**Phase:** MVP | **Priority:** P1 | **Estimate:** M (1–2 days)

## Context

Currently `register` records the asset's SHA-256 and metadata in a manifest
but does not store the asset bytes anywhere. The manifest points at an asset
by hash; to retrieve or watermark the asset later, the bytes must be
findable.

ARCHITECTURE.md (Layer 6) specifies a `vault/assets/<sha256>` layout — a flat
directory where each file is named by its content hash. This avoids filenames
entirely (the hash is the locator) and makes the store append-only: you cannot
accidentally overwrite a registered asset with different bytes.

## Acceptance Criteria

- [ ] `register --ingest` copies the asset into `vault/assets/<sha256>` using
      the hash as the filename (no extension). Without `--ingest`, behaviour
      is unchanged from PoC.
- [ ] The CAS directory is listed under `asset.storage` in the manifest as
      `{"scheme": "local-cas", "locator": "vault/assets/<sha256>"}`.
- [ ] `vault/assets/` is in `.gitignore` (assets never go to git; already
      present but verify it covers this path).
- [ ] A helper `provenance.py locate <sha256>` prints the absolute path to
      the asset in the CAS if present, or exits non-zero.
- [ ] Re-running `register --ingest` on an already-ingested asset is
      idempotent (checks that the file at `vault/assets/<sha256>` hashes
      correctly before declaring success).

## Definition of Done

- Acceptance criteria pass.
- Ingestion is confirmed not to bloat the git working tree (CI smoke can
  check `git status` after `register --ingest` and assert vault/assets
  is not staged).
- CHANGELOG updated.

## Estimate

M — ~1.5 days: copy logic, CAS integrity check, manifest field update,
locate command, test for idempotency.

## Dependencies

- None (independent of T-001/T-002, but designed to hold assets that T-005
  watermarking will read).

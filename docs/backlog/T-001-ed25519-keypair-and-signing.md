# T-001 — Ed25519 keypair generation and manifest signing

**Phase:** MVP | **Priority:** P0 | **Estimate:** M (1–2 days)

## Context

The PoC writes the `signature` field as reserved (`null`). Without a real
signature, any party with write access to the ledger can alter a manifest's
`creator`, `license`, or `creation` fields after the fact. The manifest's
`chain.prev` linkage is meaningless without a signature tying the chain to a
specific key.

Ed25519 is the algorithm already specified in the JSON Schema
(`"algorithm": {"enum": ["ed25519"]}`). It is available in Python's
`cryptography` package and produces compact, fast-to-verify signatures. This
task generates the key and signs; T-002 adds verification.

## Acceptance Criteria

- [ ] `python src/provenance.py keygen` generates an Ed25519 keypair, stores
      the private key at `~/.apv/signing.key` (or a path from `APV_KEY_PATH`
      env var) with mode 0600, and prints the public key fingerprint in
      `ed25519:<hex>` format.
- [ ] `register` reads the private key, signs the canonical manifest
      (sorted-key, compact JSON, `signature` field absent from the payload),
      and writes the base64-encoded signature into `manifest.signature.value`.
- [ ] If no key file exists, `register` warns clearly and proceeds unsigned
      (backward-compatible with PoC).
- [ ] The private key file is listed in `.gitignore` and never committed.
- [ ] ADR-0002 written covering the Ed25519 + `cryptography` lib decision.

## Definition of Done

- Acceptance criteria all pass.
- `ruff check src/` clean with new module.
- CI smoke test still passes (key not present → unsigned, no crash).
- CHANGELOG updated under `[Unreleased]`.
- `schemas/manifest.schema.json` unchanged (signature field already defined).

## Estimate

M — ~2 days: keygen plumbing, canonical serialisation under signing, key
permission check, tests for signed vs unsigned path.

## Dependencies

- None (this is the prerequisite for T-002).
- `cryptography` package added to requirements.txt (triggers ADR).

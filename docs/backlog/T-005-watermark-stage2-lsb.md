# T-005 — Watermark Stage 2: key-seeded LSB with ECC payload

**Phase:** MVP | **Priority:** P1 | **Estimate:** L (3–5 days)

## Context

Stage 2 embeds a robust-ish payload — the manifest hash plus a recipient
identifier — into the least-significant bits of pixel channels at
key-seeded pseudorandom positions. Reed-Solomon or BCH error-correcting
code is applied to the payload so that minor bit-flip noise does not destroy
extractability.

ARCHITECTURE.md is honest: Stage 2 survives lossless copying only. JPEG
re-compression at any quality level, or even a single crop-and-save, will
destroy the LSB payload. This is explicitly documented in tests
(the test for "JPEG re-encode → extraction fails" is a required acceptance
criterion, not an edge case to hide).

Stage 2 is meaningful for lossless distribution channels: providing PNG
originals to trusted licensees, archival deposits, and print-on-demand
pipelines that preserve pixel data. Combined with Stage 4 per-recipient
variants (v1), Stage 2 allows tracing which exact copy was leaked even from
a lossless chain.

## Acceptance Criteria

- [ ] `watermark stage2 <sha256> [--recipient <id>]` embeds a 64-byte payload
      (32-byte manifest hash + 32-byte recipient ID, zero-padded) at
      key-seeded positions into the PNG image. Key derived from
      `HMAC-SHA256(embedding_key, manifest_sha256)`.
- [ ] `watermark extract2 <file>` extracts and decodes the payload from a
      file, printing the embedded manifest hash and recipient ID.
- [ ] Round-trip test: embed → lossless PNG re-save → extract succeeds.
- [ ] Documented failure test: embed → JPEG re-encode → extract fails
      (error recorded in test output, not hidden).
- [ ] Embedding key is stored as `key_id` in `watermarks[]` (never the raw
      key). The actual key lives in `~/.apv/wm.key` (separate from the
      signing key).
- [ ] NumPy is the only additional dependency beyond Pillow (T-004).

## Definition of Done

- Acceptance criteria all pass.
- Published robustness note in test output (JPEG failure is expected and shown).
- ROADMAP.md MVP criterion "Round trip: Stage 2 watermark embedded → ..." passes.
- CHANGELOG updated; ADR-0004 for NumPy addition.

## Estimate

L — ~4 days: ECC library selection (Python `reedsolo` or custom BCH), key
derivation, position seeding, embed/extract symmetry, PNG round-trip test,
documented JPEG failure test.

## Dependencies

- T-003 (CAS access).
- T-004 (establishes the `watermarks[]` manifest update pattern).
- NumPy, Pillow in requirements.

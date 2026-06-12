# T-002 — Signature verification in `verify` command

**Phase:** MVP | **Priority:** P0 | **Estimate:** S (half a day)

## Context

After T-001 ships signed manifests, `verify` must check the signature or the
signing step adds no security value. Verification requires the creator's
public key. The manifest carries a `creator.public_key_fingerprint`; the
actual public key must be resolvable — initially from a local key-store or
passed on the command line.

A tampered manifest (altered creator, license, or chain fields) must fail
verification with a clear, machine-parsable error code, not a silent pass.
This is one of the MVP acceptance criteria in ROADMAP.md.

## Acceptance Criteria

- [ ] `verify` extracts `signature.value` and `creator.public_key_fingerprint`
      from the manifest.
- [ ] It resolves the public key via: `--pubkey <file>` flag, or the local
      key-store at `~/.apv/keys/<fingerprint>.pub`, or the same private-key
      file's embedded public portion.
- [ ] Verification recomputes the canonical manifest bytes (signature field
      removed) and checks the Ed25519 signature. Success → exit 0 with
      `VERIFIED (signed)` output. Failure → exit 3 with `SIGNATURE INVALID`
      and both the stored fingerprint and the actual key used.
- [ ] If the manifest has no `signature` field (unsigned PoC manifest),
      `verify` exits 0 with `VERIFIED (unsigned — MVP signing not applied)`.
- [ ] A manifest whose `signature.value` was base64-corrupted or whose
      content was altered after signing fails exit-3 in the test suite.

## Definition of Done

- All acceptance criteria pass.
- The documented MVP acceptance criterion "A manifest tampered with after
  signing fails verify with a signature error" passes as an automated test.
- Structured log entry emitted on verification failure (see OBSERVABILITY.md).
- CHANGELOG updated.

## Estimate

S — ~4 hours: signature check logic is ~20 lines once T-001 is done; most
time is in the failure-path tests and structured logging.

## Dependencies

- T-001 must be complete (signed manifests must exist to verify).

# Roadmap

Three phases. Each phase has explicit acceptance criteria — a phase is done
when every criterion passes, not when the calendar says so.

## Phase 1 — PoC (this repository)

**Goal:** prove the hash → manifest → git-commit loop end to end with zero
installation friction, and pin down the manifest contract.

**Scope**

- `src/provenance.py` CLI: `register`, `verify`. Stdlib only.
- `schemas/manifest.schema.json` as the manifest contract (draft 2020-12).
- Architecture and legal-landscape documentation.

**Acceptance criteria**

- [ ] `python src/provenance.py register <file>` on a fresh repo produces a
      schema-valid manifest in `vault/manifests/` and exactly one git commit
      containing it.
- [ ] `verify <file>` exits 0 with a human-readable summary when the file is
      unmodified, and exits non-zero naming both hashes when even one byte
      changed.
- [ ] Registering a second work by the same creator sets `chain.prev` to the
      first manifest's sha256.
- [ ] Works on Windows and Linux paths, including directories containing
      spaces and brackets.
- [ ] CI green: `py_compile` lint + schema validates as draft 2020-12.

## Phase 2 — MVP

**Goal:** make the ledger trustworthy against forgery (signatures), make
assets durable (CAS), and ship the first two watermark stages.

**Scope**

- Ed25519 keypair generation; detached signatures over canonicalized
  manifests; `verify` checks signature and chain linkage.
- Local content-addressed asset store (`vault/assets/<sha256>`), with
  `register` optionally ingesting the asset alongside the manifest.
- Watermark Stage 1 (XMP/PNG-text manifest pointer) and Stage 2 (key-seeded
  LSB with error-correcting code) for PNG; `watermarks[]` records written.
- Derivation queries: `lineage <sha256>` walks `parent_works` and
  `chain.prev` and prints the DAG.
- SQLite index over manifests for fast lookup (rebuildable from the ledger —
  the index is a cache, git remains the source of truth).

**Acceptance criteria**

- [ ] A manifest tampered with after signing fails `verify` with a signature
      error; a manifest re-signed by a different key fails creator-identity
      check.
- [ ] Round trip: Stage 2 watermark embedded → file re-saved losslessly →
      payload extracted intact; and the documented failure (JPEG re-encode →
      extraction fails) is demonstrated in tests, not hidden.
- [ ] `lineage` correctly renders a 3-generation derivation chain created in
      tests.
- [ ] Deleting the SQLite index and rebuilding from git yields identical
      query results.
- [ ] All PoC criteria still pass (no regressions in the core loop).

## Phase 3 — v1

**Goal:** interoperate (C2PA), trace leaks (Stages 3–4), and give the ledger
independent witnesses (anchoring) plus a usable surface (API/dashboard).

**Scope**

- C2PA export (APV manifest → embedded Content Credentials) and import.
- Watermark Stage 3 (DCT/DWT spread-spectrum) and Stage 4 (per-recipient
  multivariant with collusion-resistant codes) — including a published
  robustness test matrix.
- Periodic Merkle-root anchoring of new manifests via OpenTimestamps (or
  equivalent transparency log); `verify` can check anchor inclusion.
- Hosted verification API (`GET /verify/<sha256>`) and a minimal creator
  dashboard.
- Own-chain feasibility study delivered as a research memo — explicitly a
  go/no-go decision point, not a commitment.

**Acceptance criteria**

- [ ] An APV-registered PNG exported with C2PA credentials validates in
      Adobe's public Verify tool.
- [ ] Stage 3 watermark survives JPEG quality 80 re-encode and 50% resize in
      ≥ 95% of the test corpus; failure modes beyond that are documented in
      the published matrix.
- [ ] Given 3 leaked variants from a 50-recipient multivariant set, tracing
      identifies the correct recipients with the false-positive bound stated
      by the code's parameters.
- [ ] An anchored manifest's timestamp is verifiable by a third party using
      only public infrastructure (no APV services online).
- [ ] Verification API p95 latency < 300 ms for ledger lookups.

## Sequencing rationale

Signatures before watermarks (MVP) because authorship claims are the legal
core; watermarks without signed manifests trace leaks of *unattributable*
works. Anchoring waits for v1 because it only adds value once there are
external relying parties; a solo creator's own clones are sufficient
witnesses during MVP.

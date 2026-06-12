# T-008 — C2PA export: APV manifest → embedded Content Credentials

**Phase:** v1 | **Priority:** P2 | **Estimate:** L (3–5 days)

## Context

ARCHITECTURE.md Layer 4 defines APV's strategic position: the vault is the
ledger; C2PA is the interchange format. C2PA Content Credentials are the
industry standard backed by Adobe, Microsoft, Google, and camera makers.

Without C2PA export, APV-registered works cannot interoperate with the growing
ecosystem of C2PA-aware tools (Adobe Firefly, cameras, social platforms). With
export, an APV creator gets both: a longitudinal ledger that survives metadata
stripping, and an in-file credential that platforms and end-users can verify
without any APV software.

The ROADMAP.md v1 acceptance criterion: "An APV-registered PNG exported with
C2PA credentials validates in Adobe's public Verify tool."

Field mapping specified in ARCHITECTURE.md Layer 4:
- `creation` → `c2pa.actions` + `cawg.training-and-data-mining`
- `creator` → `cawg.identity` / schema.org `CreativeWork` author
- `license` → custom `art.apv.license` assertion (SPDX string)
- `parent_works` → C2PA ingredient assertions
- `asset.sha256` → C2PA hard binding (hash assertion)

## Acceptance Criteria

- [ ] `python src/provenance.py c2pa export <sha256>` reads the manifest and
      uses the `c2pa-python` library (or `c2pa-rs` via subprocess) to embed
      Content Credentials into a copy of the asset.
- [ ] All four field mappings from ARCHITECTURE.md Layer 4 are present in the
      exported manifest store.
- [ ] The exported file validates in Adobe's public C2PA Verify tool
      (https://verify.contentauthenticity.org/) — screenshot captured in CI
      artefact or documented in acceptance test notes.
- [ ] The original APV manifest in the ledger is unchanged; export is
      read-only with respect to the vault.
- [ ] ADR-0005 documents the C2PA library choice and binding strategy.

## Definition of Done

- Acceptance criteria pass.
- Validation screenshot or automated c2pa-verify output stored in
  `tests/fixtures/c2pa-validate-output.txt`.
- CHANGELOG updated; ROADMAP v1 C2PA criterion marked.

## Estimate

L — ~4 days: C2PA library evaluation, field mapping implementation,
assertion serialisation, validation test, ADR.

## Dependencies

- T-001/T-002 (signed manifests — C2PA requires a valid signing key).
- T-003 (CAS — need asset bytes for embedding).
- C2PA Python library or Rust binding to be selected in ADR-0005.

# T-004 — Watermark Stage 1: XMP/PNG-text manifest pointer

**Phase:** MVP | **Priority:** P1 | **Estimate:** S (half a day)

## Context

Stage 1 is the simplest watermark: embed a pointer to the APV vault and
manifest hash inside the image's own metadata fields. For PNG, this means
a `tEXt` or `iTXt` chunk; for JPEG, an XMP packet; for TIFF, an IPTC or
XMP record. Pillow handles all three.

ARCHITECTURE.md is explicit that Stage 1 robustness is zero — one call to
`exiftool -all=` strips it. Stage 1 is not adversarial defence; it is
cooperative-platform discovery. When an APV-registered image is uploaded to
a platform that reads metadata (social networks, stock sites, DAMs), the
platform can link back to the ledger entry without scraping.

Every embedded watermark must produce a `watermarks[]` entry in the manifest.
That ledger record is the authoritative source of what was embedded; the
embedded metadata is just a convenience pointer back to it.

## Acceptance Criteria

- [ ] `python src/provenance.py watermark stage1 <sha256>` embeds a pointer
      `{"apv_vault": "<vault_url>", "manifest": "<manifest_sha256>"}` into a
      PNG or JPEG asset retrieved from the CAS (requires T-003).
- [ ] The watermarked file is written to `vault/assets/<sha256>-wm1.<ext>` and
      its own SHA-256 recorded in the `watermarks[].variant_sha256` field.
- [ ] A `watermarks[]` entry is appended to the manifest:
      `stage=1, algorithm="xmp-pointer-v1"`, `embedded_at` timestamp,
      `payload_sha256` = hash of the JSON pointer object.
- [ ] The manifest is re-committed to the ledger with the new watermarks entry.
- [ ] Pillow is the only new dependency introduced by this task.

## Definition of Done

- Acceptance criteria pass.
- Test: read back the embedded metadata from the output file and verify it
  matches the manifest pointer before and after lossless PNG re-save.
- ADR-0003 noting Pillow addition.

## Estimate

S — ~4 hours: Pillow chunk writing is straightforward; the manifest
re-commit flow is already established.

## Dependencies

- T-003 (CAS store — watermarked asset must come from and write to CAS).
- T-001 recommended (re-committing the manifest should use a signature) but
  not strictly blocking.

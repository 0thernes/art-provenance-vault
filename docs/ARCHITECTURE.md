# Architecture

Art Provenance Vault (APV) is a layered system. Each layer is independently
useful, independently replaceable, and makes a *narrow* claim. The system's
overall trust guarantee is the composition of those narrow claims — not a
single monolithic promise. This document describes each layer, what it
guarantees, and — just as important — what it does **not**.

> **IP-protection strategy.** The five-pillar protection stack — invisible
> watermark fallback, blockchain ledger, extensive per-file metadata, human-
> authorship layering (2-of-3 human majority), and public-repo durable storage
> — is the conceptual foundation this architecture implements. The full thesis,
> with the legal reality check and design disclaimers, lives in
> [IP-STRATEGY.md](IP-STRATEGY.md). Read it alongside this document.

```
Layer 6  Anchoring (optional)     Merkle root of manifests → public chain
Layer 5  Watermarking             4-stage embed pipeline, per-recipient variants
Layer 4  Standards alignment      manifest fields ↔ C2PA assertions
Layer 3  Tamper evidence          git commit DAG as hash-chained ledger
Layer 2  Manifests                one signed JSON document per artwork
Layer 1  Identity                 SHA-256 of asset bytes
─────────────────────────────────────────────────────────────────────────
Assets   content-addressed bulk storage, referenced by hash (NOT in git)
```

## Layer 1 — Content Identity: SHA-256

The identity of an artwork is the SHA-256 digest of its exact bytes. Not its
filename, not its EXIF, not a perceptual fingerprint — the bytes.

**What this gives us**

- A stable, globally unique, independently recomputable identifier.
- Verification requires nothing but the file and a hash function: no APV
  software, no network, no registry lookup.
- SHA-256 has no known practical collision or preimage attacks; it is the
  hash C2PA, Sigstore, and every major transparency log already use.

**What this does not give us**

- **No similarity detection.** Re-encoding a PNG as JPEG produces a new
  identity. That is intentional: byte identity is the anchor; *derivative*
  relationships are expressed explicitly in the manifest (`parent_works`),
  and perceptual matching is a discovery feature for later phases, never a
  trust primitive.
- **No authorship.** A hash proves *what*, never *who*. Authorship comes
  from Layer 2 signatures.

## Layer 2 — The Manifest

One JSON document per artwork, conforming to
[`schemas/manifest.schema.json`](../schemas/manifest.schema.json). The
manifest is the unit of provenance. Core fields:

| Field | Purpose |
|-------|---------|
| `asset.sha256` | Layer 1 identity of the artwork bytes |
| `creator` | Human/entity claiming authorship (id, name, public key fingerprint) |
| `creation` | How it was made: tool/model, model version, prompt record, human contribution statement |
| `human_attestations[]` | Signed, timestamped records of each human approval layer (pre- and post-generation) — the evidentiary core of the human-authorship strategy. See [IP-STRATEGY.md](IP-STRATEGY.md) Pillar 4. |
| `ai_generation` | Structured record of the AI generation event: model, prompt reference, generation params (seed, sampler, steps). Complements `creation.tools` with the specific machine-stage parameters. |
| `parent_works[]` | Hashes of works this one derives from → a derivation DAG across manifests |
| `license` | SPDX expression plus optional commercial terms reference |
| `watermarks[]` | Records of every watermark embedded in distributed copies (Layer 5) |
| `ledger_anchor` | Chain identifier, tx/Merkle reference, and anchor timestamp for the Pillar-2 public ledger entry. See [IP-STRATEGY.md](IP-STRATEGY.md) Pillar 2. |
| `chain.prev` | sha256 of the previous manifest by this creator → an intra-creator chain *inside* the data, independent of git |
| `signature` | Detached signature over the canonicalized manifest (reserved in PoC, Ed25519 in MVP) |

Design decisions worth defending:

- **JSON, canonicalized before signing.** We sign the JCS-style canonical
  form (sorted keys, no insignificant whitespace) so that pretty-printing
  does not break signatures. The PoC writes sorted-key JSON for this reason
  even before signing exists.
- **`chain.prev` duplicates what git does — deliberately.** If a manifest
  set is exported *out* of git (to IPFS, to a C2PA sidecar, to a court
  filing), the chain linkage survives, because it lives in the data, not in
  the transport.
- **Prompts are first-class provenance.** For AI-assisted work, the model
  identifier, version/hash if available, and the prompt chain are recorded.
  Creators who consider prompts trade secrets may record a salted hash of
  the prompt instead (`prompt_sha256`) — provable later, private now.
- **Human contribution is a stated claim, not an inferred score.** The
  `creation.human_contribution` field is a free-text declaration. APV
  records claims and makes them non-repudiable; it does not adjudicate them.
  This matters legally (see [LEGAL-NOTES.md](LEGAL-NOTES.md)) — copyright
  offices care about human authorship, and a contemporaneous signed declaration
  is far stronger evidence than a retroactive one.
- **Human attestations add structure to that claim.** `human_attestations[]`
  breaks the creation process into two explicit human stages — pre-generation
  direction (layer 1) and post-generation editing and approval (layer 2) —
  each with a timestamped, signed record. This 2-of-3 human-majority design
  ensures human creative control is documented at both ends of the AI
  generation event. The legal implications are analyzed in
  [IP-STRATEGY.md](IP-STRATEGY.md) Pillar 4.

## Layer 3 — Git as the Tamper-Evidence Ledger

Every manifest is committed to a git repository ("the vault"). Git commits
form a Merkle DAG: each commit hashes its tree and its parent commit. Once a
manifest is committed, altering it — or reordering history before it —
changes every subsequent commit hash.

**Why git and not a database or a custom ledger**

- The hash-chain property we need is exactly what git already implements,
  with 20 years of hardening and universal tooling.
- Every `git clone` is a full replica of the ledger. Tamper evidence
  improves with each independent clone — collaborators, CI, a notary
  service — because rewriting history would require corrupting all of them.
- Commit timestamps plus the chain give us *ordering* for free. A manifest
  committed before a dispute arose is strong evidence the record predates
  the dispute.
- Auditing requires `git log`, nothing proprietary. If APV-the-company
  disappears, every vault remains fully verifiable.

**Honest limits**

- Git's internal object hashing is SHA-1 (hardened SHA-1 in modern git, with
  collision detection; SHA-256 object format exists but has limited hosting
  support). We therefore do **not** rely on git's object hash as a
  cryptographic claim: the manifest's own `chain.prev` (SHA-256) and the
  Layer 6 Merkle anchor carry the cryptographic weight. Git provides
  *structure and replication*; SHA-256 provides *strength*.
- A sole holder of a vault can rewrite it. Tamper *evidence* requires a
  witness: a second clone, a signed tag held by a third party, or an
  anchor (Layer 6). The PoC is honest about this: it proves the mechanism,
  not the witnessing infrastructure.
- Commit timestamps are self-asserted. Trustworthy time comes from anchoring
  or from RFC 3161 timestamps in later phases.

## Layer 4 — C2PA Alignment, Not Reinvention

[C2PA Content Credentials](https://c2pa.org/) is the industry standard for
content provenance, backed by Adobe, Microsoft, Google, and camera makers. It
would be strategically foolish to compete with it and technically foolish to
ignore the problems it has already solved (canonical serialization,
certificate trust lists, soft bindings).

APV's position: **the vault is the ledger; C2PA is the interchange format.**

- Every APV manifest field maps to a C2PA assertion:
  `creation` → `c2pa.actions` / `cawg.training-and-data-mining`,
  `creator` → `cawg.identity` / `stds.schema-org.CreativeWork` author,
  `license` → a custom `art.apv.license` assertion carrying the SPDX string,
  `parent_works` → C2PA ingredient assertions,
  `asset.sha256` → the C2PA hard binding (hash assertion).
- v1 ships an exporter (manifest → C2PA manifest store embedded in the
  asset) and an importer (C2PA-signed asset → APV manifest).
- What APV adds that C2PA alone does not: a **longitudinal ledger**. C2PA
  travels with one file and dies when metadata is stripped; the vault is an
  out-of-band record that survives stripping, records the *creator's whole
  body of work* as a chain, and supports leak tracing via Layer 5.

## Layer 5 — Invisible Watermark Pipeline (specification)

Watermarking is specified here and implemented from MVP onward. Four stages,
escalating in robustness and cost. Every embedded watermark is recorded as a
`watermarks[]` entry in the manifest: stage, algorithm, payload hash, key id,
recipient binding.

**Stage 1 — Metadata embedding.** Manifest pointer (vault URL + manifest
hash) written into XMP/EXIF/PNG-text chunks.
*Robustness: none — stripped by any re-encode or by `exiftool` in one
command. Value: cooperative-platform discovery, not adversarial defense.*

**Stage 2 — Spatial LSB.** Payload (manifest hash + recipient id, ECC-coded)
embedded in least-significant bits of pixel channels, key-seeded positions.
*Robustness: survives lossless copying only. JPEG compression, resizing, or
even slight noise destroys it. Value: tamper detection on lossless
distribution channels, and a cheap first tracing layer.*

**Stage 3 — Frequency domain (DCT/DWT).** Payload embedded in mid-frequency
DCT or DWT coefficients, spread-spectrum, key-seeded.
*Robustness: survives moderate JPEG re-compression, mild resizing, small
crops — the classic Cox et al. spread-spectrum tradeoff. Does NOT reliably
survive aggressive crops, heavy filtering, print-scan, or AI re-generation
(img2img at high strength launders any current watermark). We state this
plainly: no invisible watermark today survives a determined, informed
attacker. The goal is raising the cost and catching the careless majority.*

**Stage 4 — Multivariant per-recipient tracing.** Each licensed recipient
receives a uniquely watermarked variant (distinct Stage 2/3 payloads, plus
sub-perceptual pixel-level variations). When a copy leaks, correlation
against the recorded variant set identifies the recipient.
*Robustness: collusion attacks (multiple recipients averaging their copies)
defeat naive schemes; v1 targets collusion-resistant codes (Tardos-style) at
spec level. Tracing yields probabilistic evidence suitable for terminating a
license relationship, not by itself for litigation.*

The honest summary we give partners: **the manifest ledger is the strong
claim; watermarks are a tracing aid with known, documented failure modes.**

## Layer 6 — Storage Reality and Anchoring

**Git is the manifest ledger, not the asset store.** This is a hard rule:

- GitHub blocks files > 100 MB and recommends repos stay under ~1–5 GB;
  art portfolios run into terabytes. Git's delta model is also pathological
  for large binaries.
- GitHub's Terms of Service allow account/content removal; a ledger whose
  bulk data can be deleted by a platform decision is not a vault. (Manifests
  are tiny, replicated by every clone, and survive platform loss.)
- Deletability cuts both ways: creators may need takedowns of *assets*
  (e.g., a work they no longer wish public) without destroying the *record*
  that the work existed. Separating manifest from asset makes that possible.

Assets therefore live in **content-addressed storage** — local CAS directory
in MVP (`vault/assets/<sha256>` layout), S3-compatible or IPFS backends as
options later. The manifest's `asset.sha256` *is* the pointer; any storage
backend that can answer "give me the bytes with this hash" is conformant.

**Blockchain anchoring is a thin optional layer, not the foundation.**
Periodically (e.g., daily), the Merkle root of all manifest hashes committed
since the last anchor is published to a public chain or a transparency log
(an OpenTimestamps attestation is the cheapest viable mechanism). This buys
third-party-verifiable timestamps with one tiny transaction per period —
without putting any artwork data, personal data, or per-work cost on-chain.

Building an own chain is explicitly a **research track**, not a dependency:
nothing in layers 1–5 requires it, and the system must remain fully
functional and verifiable with git + SHA-256 alone.

## Data Flow (PoC scope)

```
register <file>:
  sha256(file) ──→ build manifest (schema-conformant, sorted keys)
              ──→ link chain.prev to creator's latest manifest
              ──→ write vault/manifests/<sha256>.json
              ──→ git add + git commit   ("ledger entry")

verify <file>:
  sha256(file) ──→ locate vault/manifests/<sha256>.json
              ──→ recompute & compare hash, report manifest summary
              ──→ (MVP+: verify signature, verify chain.prev linkage)
```

## Decisions Log

Architecture decisions are recorded as ADRs in [`docs/adr/`](adr/).
ADR-0001 establishes the process; substantive decisions in this document
(git-as-ledger, C2PA alignment, stdlib-only PoC) will be back-filled as
ADRs 0002+ as they come under pressure from real implementation work.

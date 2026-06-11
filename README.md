# Art Provenance Vault

**Tamper-evident provenance, IP licensing, and watermarking for AI-assisted art — built on git as the ledger.**

## Vision

Every piece of AI-assisted art should carry a verifiable, portable record of who made it, how it was made, what it derives from, and under what terms it may be used. Art Provenance Vault (APV) turns that record into infrastructure: a signed manifest per artwork, chained into a git history that anyone can audit, aligned with the C2PA Content Credentials standard, and reinforced by a layered invisible-watermark pipeline for leak tracing.

## Problem

AI-generated and AI-assisted artwork is exploding in volume while the trust layer around it collapses:

- **Attribution is unverifiable.** A PNG carries no reliable record of its creator, the model used, the prompts involved, or the human contribution — metadata is trivially stripped.
- **Licensing is ambiguous.** Buyers, platforms, and downstream creators cannot tell what license applies to a work or whether the seller has the right to license it at all.
- **Derivation chains are invisible.** Works built on other works (img2img, inpainting, LoRA fine-tunes) lose their lineage the moment they are exported.
- **Leaks are untraceable.** When a licensed work appears outside its licensed context, the creator has no way to identify which recipient leaked it.
- **Existing registries are silos.** Centralized provenance databases die with the company that runs them, and their records cannot be independently verified.

## Solution

APV combines four well-understood primitives into one coherent system:

1. **Content hashing** — every asset is identified by its SHA-256 digest. The hash, not the filename, is the artwork's identity.
2. **Signed JSON manifests** — one manifest per artwork records creator, creation chain (model, prompts, parent works), license (SPDX expression), and watermark records. Manifests map onto C2PA assertions so they interoperate with the industry standard instead of competing with it.
3. **Git as the tamper-evidence layer** — each manifest is committed to a git repository. Git's commit DAG is a hash chain: rewriting history is detectable, and any clone is a full, independently verifiable replica of the ledger.
4. **Layered invisible watermarking** — a staged pipeline (metadata → spatial LSB → frequency-domain DCT/DWT → per-recipient multivariant) embeds traceable marks into distributed copies, enabling leak attribution.

Git stores the **manifests**, not the artworks. Bulk assets live in content-addressed storage that the manifest points to by hash. Optional periodic anchoring of a Merkle root into a public blockchain adds third-party timestamping without making the system depend on a chain.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  Layer 6  Anchoring (optional)   Merkle root → chain    │
│  Layer 5  Watermarking           4-stage pipeline        │
│  Layer 4  Standards alignment    manifest ↔ C2PA         │
│  Layer 3  Tamper evidence        git commit hash chain   │
│  Layer 2  Manifests              signed JSON per work    │
│  Layer 1  Identity               SHA-256 of asset bytes  │
└─────────────────────────────────────────────────────────┘
         Assets ──→ content-addressed storage (not git)
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full design, including honest robustness limits of each watermarking stage and the storage reality check.

## MVP Scope

The PoC in this repository proves the core loop end to end with **zero dependencies beyond Python 3.10+ and git**:

- `python src/provenance.py register <file>` — hash an asset, generate its manifest, commit it to the ledger.
- `python src/provenance.py verify <file>` — re-hash the asset and verify it against the recorded manifest.
- A real JSON Schema ([schemas/manifest.schema.json](schemas/manifest.schema.json)) defining the manifest contract.

Out of scope for the PoC: cryptographic signatures (manifest field reserved), watermark embedding (specified in architecture, implemented in MVP phase), C2PA binary serialization, and any UI.

## Roadmap (Phased)

| Phase | Focus | Status |
|-------|-------|--------|
| **PoC** | Hash → manifest → git commit loop; schema; verify command | ✅ This repo |
| **MVP** | Ed25519 manifest signing; stage 1–2 watermarking; content-addressed asset store; derivation-chain queries | Planned |
| **v1** | C2PA export/import; stage 3–4 watermarking; Merkle-root anchoring; hosted verification API; creator dashboard | Planned |

Detailed acceptance criteria per phase: [docs/ROADMAP.md](docs/ROADMAP.md).

## Tech Stack

- **PoC:** Python 3.10+ standard library only (`hashlib`, `json`, `argparse`, `subprocess`), git ≥ 2.28.
- **MVP targets:** `cryptography` (Ed25519), Pillow + NumPy (watermarking), SQLite index over the manifest ledger.
- **Standards:** SHA-256 (FIPS 180-4), SPDX license expressions, JSON Schema draft 2020-12, C2PA 2.x assertion model.

## Project Status

**Pre-seed / proof-of-concept.** The provenance ledger loop is working code; watermarking and signing are specified at design level. This repository is the canonical reference for the architecture and the demonstration vehicle for investor and partner conversations.

## Repository Layout

```
docs/            Architecture, roadmap, legal research notes, ADRs
schemas/         JSON Schema for the artwork manifest
src/             PoC CLI (provenance.py)
.github/         CI workflow (lint + schema validation)
```

## License

MIT — see [LICENSE](LICENSE). The MIT license covers this software; artwork manifests carry their own per-work SPDX license expressions.

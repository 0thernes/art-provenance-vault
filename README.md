# Art Provenance Vault

**Tamper-evident provenance, IP licensing, and watermarking for AI-assisted art — built on git as the ledger.**

[![CI](https://github.com/0thernes/art-provenance-vault/actions/workflows/ci.yml/badge.svg)](https://github.com/0thernes/art-provenance-vault/actions/workflows/ci.yml)
[![CodeQL](https://github.com/0thernes/art-provenance-vault/actions/workflows/codeql.yml/badge.svg)](https://github.com/0thernes/art-provenance-vault/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Status: PoC](https://img.shields.io/badge/status-PoC-orange)

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

## IP-Protection Strategy (Five Pillars)

APV implements a five-pillar protection stack designed so that stripping any
one layer of protection does not eliminate the authorship claim:

| Pillar | Mechanism | Purpose |
|--------|-----------|---------|
| **1 — Invisible watermark** | 4-stage pipeline embedded in signal | Fallback when visible mark is stripped |
| **2 — Blockchain ledger** | Merkle root anchored to public chain or OTS | Permanent, third-party timestamp; survives platform loss |
| **3 — Per-file metadata** | Signed manifest with full creation chain | Extensive context to prove authorship in a legal contest |
| **4 — Human-authorship layering** | 2-of-3 human stages wrapping AI generation | Auditable evidence of genuine human creative control |
| **5 — Public repo storage** | Git vault cloneable by anyone | Distributed, decentralized ledger; no single authority |

The full thesis — including an honest legal reality check on the 2-of-3
human-majority heuristic versus current US Copyright Office guidance and the
*Thaler v. Perlmutter* line of cases — is in
[docs/IP-STRATEGY.md](docs/IP-STRATEGY.md).

> **Design strategy, not legal advice.** This system produces tamper-evident
> provenance records and auditable human-authorship evidence. It does not
> certify that any work is copyrighted and does not constitute legal counsel.

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

## Project Board

Development is tracked in [docs/KANBAN.md](docs/KANBAN.md) with WIP-limited
columns (Backlog / Ready / In Progress / In Review / Done). Detailed card
files for the highest-priority MVP work live in [docs/backlog/](docs/backlog/).

## Quality and Audit

| Document | Purpose |
|----------|---------|
| [docs/IP-STRATEGY.md](docs/IP-STRATEGY.md) | Five-pillar IP-protection strategy: invisible watermark, blockchain ledger, per-file metadata, human-authorship layering (2-of-3 design + legal reality check), public-repo storage |
| [docs/AUDIT.md](docs/AUDIT.md) | Gold-standard self-audit checklist (35+ items across Correctness, Security, Provenance Integrity, Performance, Reproducibility, Tests, Docs, Licensing) |
| [docs/TESTING.md](docs/TESTING.md) | Test strategy: pyramid, levels, coverage targets, CI gating |
| [docs/OBSERVABILITY.md](docs/OBSERVABILITY.md) | Structured JSON log schema, log levels, `logs/` convention, key metrics |
| [docs/SECURITY-NOTES.md](docs/SECURITY-NOTES.md) | Defensive security posture: assets, trust boundaries, risk mitigations for manifest forgery, key compromise, ledger rewrite, and watermark removal |
| [docs/CASE-STUDY-ARTIST-ZERO.md](docs/CASE-STUDY-ARTIST-ZERO.md) | Artist Zero case study: mapping the 0thernes public provenance trail (Medium third-party attribution, CC GitHub repo, PromptBase listing, NFT markets) onto APV manifest fields with a worked example manifest |

## License

MIT — see [LICENSE](LICENSE). The MIT license covers this software; artwork manifests carry their own per-work SPDX license expressions.

# Frequently Asked Questions

## What exactly does Art Provenance Vault do?

APV registers AI-assisted and human artworks in a tamper-evident ledger so
that their creator, creation method, license, and derivation history cannot be
quietly altered or denied later. Each artwork gets a SHA-256-identified
manifest committed to a git repository. Git's commit DAG — a hash chain — means
that altering any manifest after the fact changes every subsequent commit hash,
making tampering detectable by anyone holding a clone.

## Why use git as the ledger instead of a blockchain or a database?

Git already implements the hash-chain property we need, has two decades of
security hardening, and every clone is a full verifiable replica. A database
is mutable by its administrator; a blockchain adds cost and complexity without
adding meaningful properties for a system whose trust anchor is the hash chain
itself. The honest summary: git is the simplest thing that works and is already
universally available. If third-party timestamping is needed, OpenTimestamps
anchoring (Layer 6) adds it without requiring a chain. See `docs/ARCHITECTURE.md`
Layer 3 for the full rationale and the honest limits.

## Is this a replacement for C2PA Content Credentials?

No — it is designed to complement C2PA, not compete with it. C2PA travels
with a single file and dies when metadata is stripped. APV maintains an
out-of-band ledger that survives stripping, records the creator's whole body
of work as a chain, and supports leak tracing through watermarks. The v1
roadmap includes a C2PA exporter so that APV-registered works also carry
in-file C2PA credentials verifiable in Adobe's Verify tool. See Kanban card
T-008.

## The manifests are not signed yet. Is the PoC useful?

Yes, with an honest scope statement. The PoC proves the hash → manifest →
git-commit loop and pins the manifest contract. It provides *integrity and
ordering* (you can prove a manifest existed before a given git commit) but not
*authorship* (anyone with push access to the vault can write any creator
field). Ed25519 signing (T-001) is the P0 MVP task precisely because authorship
without a signature is a claim, not a proof.

## What happens when I change a file after registering it?

`verify` recomputes the SHA-256 of the current file bytes. If they do not
match the manifest, it exits non-zero and prints both the expected hash (from
the ledger) and the actual hash (from the current file). The manifest in the
ledger is not updated — a changed file is a different artwork and should be
registered separately with a `parent_works` reference to the original.

## Can someone erase or rewrite the ledger?

A sole holder of the vault with `git push --force` rights can rewrite their
own copy. Tamper evidence is proportional to how many independent clones exist.
A creator clone + a CI/CD runner clone + a trusted-notary clone makes
rewriting all three undetected essentially impossible. Layer 6 (Merkle-root
anchoring via OpenTimestamps) adds third-party-verifiable timestamps without
any APV infrastructure dependency. This is the honest account; the PoC is
upfront about it in ARCHITECTURE.md Layer 3.

## How robust is the watermarking?

Stage 1 (metadata): zero adversarial robustness — stripped by `exiftool -all=`.
Stage 2 (LSB): survives lossless copying; destroyed by JPEG compression, crop,
or resize. Stage 3 (DCT/DWT, v1): survives moderate JPEG re-encoding and mild
resize; does NOT reliably survive aggressive transforms, print-scan, or AI
re-generation at high strength. Stage 4 (multivariant per-recipient, v1):
probabilistic leak tracing against the careless majority; collusion attacks
(averaging multiple recipients' copies) require deliberate coordination.

No invisible watermark today survives a determined, informed attacker with
access to modern image processing tools. APV documents this plainly. The
watermark pipeline raises the cost and catches the careless majority; the
signed manifest ledger is the strong legal claim.

## What license does APV itself use?

MIT — see `LICENSE`. The MIT license covers the APV software. Each registered
artwork carries its own per-work SPDX license expression in the manifest's
`license.spdx` field; those are set by the creator, not inherited from APV.

## How do I contribute?

Read `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md` first. Open an issue before
starting a change, especially for anything that touches the manifest schema
(requires a version bump and migration path) or adds a dependency (requires an
ADR). The bar for scope is deliberately tight during the PoC phase.

## What is the current status of the project?

**Pre-seed / proof-of-concept.** The hash → manifest → git ledger loop is
working code. Ed25519 signing, watermarking, and C2PA alignment are specified
in architecture and on the Kanban board but not yet implemented. This
repository is the canonical reference for the design and the demonstration
vehicle for investor and partner conversations.

## Where can I follow the development roadmap?

`docs/ROADMAP.md` defines the three phases (PoC → MVP → v1) with explicit
acceptance criteria. `docs/KANBAN.md` tracks near-term implementation cards.
`docs/backlog/` contains detailed card files for the highest-priority work.
CHANGELOG.md records every version and notable unreleased change.

## Is there a way to verify a work without installing APV?

For the PoC: yes. `git clone <vault>`, then compute `sha256sum <asset>` and
check whether `vault/manifests/<hash>.json` exists and the `asset.sha256`
field matches. No APV software needed. In v1, the hosted verification API
(`GET /verify/<sha256>`) and C2PA credentials will add more convenient
verification paths.

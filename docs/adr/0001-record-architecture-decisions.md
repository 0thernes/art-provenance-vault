# ADR-0001: Record Architecture Decisions

- **Status:** Accepted
- **Date:** 2026-06-11
- **Deciders:** 0thernes

## Context

Art Provenance Vault is a trust product: its value rests on design decisions
(hash choice, ledger substrate, standards alignment, watermark claims) being
defensible years after they were made — to partners, auditors, and possibly
courts. A solo-founder project is especially vulnerable to losing the *why*
behind a decision, and an investor diligence process will ask for exactly
that record.

There is also a pleasing symmetry: a provenance product should practice
provenance on itself. Decisions, like artworks, deserve a tamper-evident,
timestamped chain.

## Decision

We will record every architecturally significant decision as an Architecture
Decision Record (ADR), following Michael Nygard's lightweight format:

- One Markdown file per decision in `docs/adr/`, numbered sequentially
  (`NNNN-short-title.md`).
- Sections: Status, Date, Context, Decision, Consequences.
- Statuses: Proposed → Accepted | Rejected; later Superseded by ADR-XXXX.
- ADRs are immutable once accepted: a change of mind is a *new* ADR that
  supersedes the old one. The git history is the audit trail.

"Architecturally significant" means: anything that changes a layer boundary
in `docs/ARCHITECTURE.md`, the manifest schema contract, a cryptographic
primitive, or an external dependency.

## Consequences

- Decision rationale survives founder context-switching and team growth.
- Diligence and security review can replay the reasoning chain instead of
  interviewing memory.
- Slight writing overhead per decision — acceptable; if a decision is not
  worth a one-page ADR, it is probably not architecturally significant.
- Candidate back-fill ADRs already identified: git-as-ledger (0002),
  C2PA-alignment-over-reinvention (0003), stdlib-only PoC constraint (0004),
  SHA-256 as identity (0005).

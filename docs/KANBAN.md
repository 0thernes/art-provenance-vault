# Kanban Board

## WIP Limits and Rationale

| Column | WIP limit | Rationale |
|--------|-----------|-----------|
| Backlog | unlimited | All scoped cards; refined before Ready |
| Ready | 5 | Prevents over-specification of work that changes before implementation |
| In Progress | 2 | Solo founder project; context-switching penalty is high |
| In Review | 3 | Review should clear quickly; a pile here signals blocked feedback |
| Done | unlimited | Archive; query by phase tag |

The trust-system nature of APV makes correctness more important than velocity.
A WIP limit of 2 on In Progress enforces focus on getting each ledger
primitive right before layering the next one on top.

---

## Board

| ID | Title | Column | Priority | Estimate |
|----|-------|--------|----------|----------|
| [T-001](backlog/T-001-ed25519-keypair-and-signing.md) | Ed25519 keypair generation and manifest signing | Backlog | P0 | M |
| [T-002](backlog/T-002-signature-verification.md) | Signature verification in `verify` command | Backlog | P0 | S |
| [T-003](backlog/T-003-local-cas-asset-store.md) | Local content-addressed asset store (`vault/assets/`) | Backlog | P1 | M |
| [T-004](backlog/T-004-watermark-stage1-metadata.md) | Watermark Stage 1 — XMP/PNG-text manifest pointer | Backlog | P1 | S |
| [T-005](backlog/T-005-watermark-stage2-lsb.md) | Watermark Stage 2 — key-seeded LSB with ECC payload | Backlog | P1 | L |
| [T-006](backlog/T-006-lineage-query-command.md) | `lineage` command — walk parent_works + chain.prev DAG | Backlog | P2 | M |
| [T-007](backlog/T-007-sqlite-manifest-index.md) | SQLite index over vault manifests (rebuildable cache) | Backlog | P2 | M |
| [T-008](backlog/T-008-c2pa-export.md) | C2PA export: APV manifest → embedded Content Credentials | Backlog | P2 | L |

### Done (PoC phase)

| ID | Title | Phase |
|----|-------|-------|
| T-000 | Hash → manifest → git-commit loop (`register` + `verify`) | PoC |
| T-000b | JSON Schema draft 2020-12 for artwork manifest | PoC |
| T-000c | CI: py_compile + ruff + schema + smoke test | PoC |

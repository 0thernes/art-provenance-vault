# T-006 — `lineage` command: walk parent_works + chain.prev DAG

**Phase:** MVP | **Priority:** P2 | **Estimate:** M (1–2 days)

## Context

The manifest schema defines two axes of DAG traversal:

1. `chain.prev` — the intra-creator time-ordered chain. Each creator's
   manifests form a linked list; following `chain.prev` backwards traces all
   works by that creator in registration order.
2. `parent_works[].sha256` — the cross-creator derivation graph. Each entry
   points at the asset hash of a work this one derives from (img2img source,
   collage component, LoRA fine-tune reference, etc.).

ROADMAP.md MVP acceptance criterion: "`lineage` correctly renders a
3-generation derivation chain created in tests." This is one of the most
legible demos for investor and partner conversations — showing that APV is not
just a single-asset stamper but a verifiable derivation graph.

## Acceptance Criteria

- [ ] `python src/provenance.py lineage <sha256>` walks both axes outward
      from the given manifest:
      - Upstream: follow `parent_works[].manifest_sha256` recursively.
      - Chain: follow `chain.prev` for the same creator.
- [ ] Output: indented tree (or ASCII DAG) showing each node as
      `<sha256[:12]> | <filename> | <creator.name> | <registered_at>`.
- [ ] Cycles (should not exist in a valid ledger, but) detected and reported
      as a ledger integrity warning rather than an infinite loop.
- [ ] `--format json` flag outputs machine-readable node/edge list for
      tooling consumers.
- [ ] Test: create 3 manifests with explicit `parent_works` linkage; assert
      `lineage` output includes all three nodes in correct order.

## Definition of Done

- Acceptance criteria pass.
- ROADMAP.md MVP criterion for lineage passes as automated test.
- No dependency on SQLite (T-007); this task reads manifest files directly.
  T-007 will later accelerate lineage queries via the index.

## Estimate

M — ~1.5 days: recursive manifest walker, cycle detection, two output
formatters, 3-generation test fixture.

## Dependencies

- None beyond existing PoC (manifests in `vault/manifests/`).
- Benefits from T-003 for full round-trips but can be tested with
  hand-crafted manifest fixtures.

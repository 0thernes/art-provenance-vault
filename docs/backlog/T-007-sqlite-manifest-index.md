# T-007 — SQLite index over vault manifests (rebuildable cache)

**Phase:** MVP | **Priority:** P2 | **Estimate:** M (1–2 days)

## Context

As the ledger grows (hundreds or thousands of manifests), linear scan over
`vault/manifests/*.json` for every `verify`, `lineage`, or future query
becomes slow. A SQLite index over the manifest fields gives O(log n) lookups
while preserving the design invariant that git is the source of truth.

ROADMAP.md acceptance criterion: "Deleting the SQLite index and rebuilding
from git yields identical query results." This is the critical property — the
index must be treated as a cache, never as the authoritative record.

The index file lives at `vault/index.db` and is gitignored.

## Acceptance Criteria

- [ ] `python src/provenance.py index rebuild` scans all `vault/manifests/*.json`
      and populates `vault/index.db` with a `manifests` table:
      `(manifest_sha256, asset_sha256, creator_id, registered_at, chain_seq,
      chain_prev, license_spdx, filename)`.
- [ ] `verify` and `lineage` both use the index when present, falling back to
      filesystem scan when `index.db` does not exist (for CI and fresh clones).
- [ ] `index rebuild` is idempotent: running it twice produces the same result.
- [ ] ROADMAP criterion: delete `vault/index.db`, rebuild, query — results
      identical to direct filesystem scan. Demonstrated as an automated test.
- [ ] `vault/index.db` is added to `.gitignore`.

## Definition of Done

- Acceptance criteria pass.
- `register` triggers `index rebuild` or an incremental insert after a
  successful commit (or documents why it does not and how to rebuild manually).
- Query benchmark: 500-manifest ledger, `verify` latency < 50 ms via index.

## Estimate

M — ~2 days: schema design, rebuild command, index-backed query paths in
`verify` and `lineage`, idempotency test, ROADMAP rebuild criterion test.

## Dependencies

- T-006 lineage command exists (index accelerates it).
- Python `sqlite3` is stdlib; no new dependencies.

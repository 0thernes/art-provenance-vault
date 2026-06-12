## Summary

<!-- What does this change do and why? One paragraph maximum. -->

## Linked Kanban card

<!-- Reference the card from docs/KANBAN.md or docs/backlog/, e.g. T-001 -->
Card: T-

## Change type

- [ ] Bug fix (non-breaking)
- [ ] Feature / acceptance-criteria work (spec it in the linked card)
- [ ] Schema change (requires manifest_version bump + migration note in CHANGELOG)
- [ ] Docs / ADR only
- [ ] CI / tooling
- [ ] Security fix (keep details minimal here; full report to 0_0@0thernes.art)

## Test evidence

<!-- What did you run to verify this? Paste or link output. -->
- [ ] `python -m py_compile src/provenance.py` passes
- [ ] `ruff check src/` clean
- [ ] Schema validates: `python -c "import json,jsonschema; ..."`
- [ ] Smoke test round-trip (register + verify + tamper) passes locally
- [ ] Any new behaviour is covered by a test or demonstrated in the smoke output

## Audit-checklist reference

<!-- If this change touches security-relevant code (manifest parsing, hash
     verification, file-path handling, signature stub), confirm against
     docs/AUDIT.md sections: Correctness, Security, Provenance Integrity. -->
- [ ] Reviewed applicable items in [docs/AUDIT.md](../docs/AUDIT.md)
- [ ] No new secrets, private keys, or credentials introduced

## Rollback note

<!-- How do we undo this if it causes problems in production/next milestone?
     For schema changes: can existing manifests still be read? -->

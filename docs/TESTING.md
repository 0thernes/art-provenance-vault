# Testing Strategy

## Philosophy

APV is a trust system. A test that passes while the ledger silently accepts
a tampered manifest is worse than no test at all — it creates false confidence
in a broken guarantee. Every test must have a clear relationship to a trust
property.

**Required properties for every acceptance test:**
1. A passing verification of a clean asset is not sufficient. There must be a
   corresponding test that a tampered or unregistered asset fails verification
   with a non-zero exit code and a useful diagnostic message.
2. Failure modes documented in ARCHITECTURE.md (Stage 2 watermark destroyed by
   JPEG re-encode; solo ledger holder can rewrite history; LSB destroyed by
   crop) must appear as explicit tests that *expect* failure, not as gaps in
   coverage.

## Test Pyramid

```
         ┌──────────────────────────────┐
         │   Integration / end-to-end   │  Few; expensive; each tests a full
         │   (register → commit → verify│  ROADMAP acceptance criterion
         └──────────────────────────────┘
       ┌────────────────────────────────────┐
       │   CLI contract tests               │  Exit codes, stdout/stderr,
       │   (subprocess invocations)         │  specific message text for trust events
       └────────────────────────────────────┘
     ┌──────────────────────────────────────────┐
     │   Unit tests                             │  Pure functions: sha256_file,
     │   (pytest, no git, no filesystem side    │  canonical(), chain_prev logic,
     │    effects beyond tmp dirs)              │  JSON schema conformance
     └──────────────────────────────────────────┘
```

## Test Levels

### Unit tests (`tests/unit/`)

- `test_hash.py` — `sha256_file` produces a known digest for a known byte
  sequence; changing one byte changes the digest.
- `test_canonical.py` — `canonical()` is deterministic across Python versions;
  key ordering is stable; adding whitespace to the input manifest does not
  change the canonical output.
- `test_chain.py` — `chain_prev()` returns `(None, 1)` for an empty vault;
  returns the correct prev hash and incremented sequence for a vault with one
  existing manifest.
- `test_schema.py` — a minimally valid manifest passes draft 2020-12
  validation; a manifest missing `required` fields fails; an invalid `sha256`
  pattern fails.

**What is mocked:** filesystem calls are exercised against `tmp_path` pytest
fixtures, not the real `vault/` directory. No `git` subprocess calls in unit
tests.

**What is real:** SHA-256 computation, JSON serialisation, schema validation.

### CLI contract tests (`tests/cli/`)

Run as subprocess calls to `python src/provenance.py` with a temporary git
repository initialised in `tmp_path`:

- `test_register_verify_roundtrip` — register a file, verify it, assert exit 0
  and `VERIFIED` in stdout.
- `test_verify_tampered` — register, flip one byte, verify, assert exit 1 and
  `FAILED` + both SHA-256 values in stderr.
- `test_verify_unregistered` — verify a file never registered, assert exit 1
  and `UNREGISTERED` in stderr.
- `test_chain_linkage` — register two files with the same creator identity;
  the second manifest's `chain.prev` equals the SHA-256 of the first manifest
  in canonical form.
- `test_already_registered_idempotent` — registering the same file twice exits
  0 without a second git commit.

### Integration / acceptance tests (`tests/acceptance/`)

These run the full loop with a real git repository and correspond 1:1 with
ROADMAP.md acceptance criteria:

| Test | Criterion |
|------|-----------|
| `test_poc_register_schema_valid` | Register produces a schema-valid manifest |
| `test_poc_verify_exact_match` | Verify exits 0 on unmodified file |
| `test_poc_verify_tampered_nonzero` | Verify exits non-zero on tampered file |
| `test_poc_chain_prev_linkage` | Second work sets chain.prev to first manifest's sha256 |
| `test_mvp_signature_forgery` (MVP) | Tampered signed manifest fails verify |
| `test_mvp_wm2_roundtrip` (MVP) | Stage 2 embed → lossless re-save → extract intact |
| `test_mvp_wm2_jpeg_failure` (MVP) | Stage 2 embed → JPEG re-encode → extract fails (expected) |
| `test_mvp_lineage_3gen` (MVP) | lineage walks a 3-generation derivation chain correctly |

## Coverage Targets

| Scope | Target | Rationale |
|-------|--------|-----------|
| `src/provenance.py` line coverage | ≥ 90% | Trust-critical CLI; untested branches are risk |
| Happy-path test without a failure-path companion | 0 allowed | Policy, not metric |
| ROADMAP acceptance criteria covered by tests | 100% | Criteria are the definition of done |

Coverage is measured with `pytest --cov=src --cov-report=term-missing`.

## Running Tests

```bash
# PoC (stdlib only, no pip beyond pytest):
pip install pytest pytest-cov
pytest tests/unit/ tests/cli/ -v

# Full suite (requires git, jsonschema):
pytest tests/ -v --cov=src --cov-report=term-missing
```

In CI (`ci.yml`), the smoke test runs as a shell script rather than pytest
because pytest is not guaranteed installed. Once `setup.cfg` / `pyproject.toml`
are added in MVP, the CI step will switch to `pytest`.

## CI Gating

- CI fails if `py_compile` or `ruff check` fail.
- The schema validation step is a required job gate.
- The smoke test (register + verify + tamper) is a required job gate.
- In MVP, `pytest` replaces the smoke script and must pass before merge.
- CodeQL analysis runs weekly and on every PR targeting `main`.

## What Is Not Tested (and Why)

| Item | Status |
|------|--------|
| Watermark robustness against adversarial transforms | Not claimed; documented failure modes only |
| Git history rewrite detection | Requires a second clone / witness; out of scope for automated tests |
| Blockchain anchor inclusion proof | Out of scope until v1 anchoring lands |
| Perceptual similarity of watermarked images | Stage 2 PSNR check in MVP; adversarial similarity out of scope |

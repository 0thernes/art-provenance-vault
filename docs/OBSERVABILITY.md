# Observability

## Overview

APV is a trust system. Its logs are not just debugging aids — they are part of
the audit record. A verification failure is a security-relevant event. A
registration of a manifest that later turns out to be a forgery attempt must
be traceable through logs. This document specifies the structured logging
schema, log levels, the `logs/` directory convention, and the key metrics the
system should emit.

## Structured Log Format

Every log record is a single JSON object on one line (`\n`-delimited NDJSON).
The logger module is `src/logging_config.py`.

### Required fields (every record)

| Field | Type | Description |
|-------|------|-------------|
| `ts` | ISO 8601 UTC string | `2026-06-11T14:30:00.123Z` — millisecond precision |
| `level` | string | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `event` | string | A short, stable, machine-readable event name (see table below) |
| `msg` | string | Human-readable description; may include dynamic values |
| `apv_version` | string | `manifest_version` constant from `provenance.py` |

### Provenance-specific fields (context-dependent)

| Field | Type | Present when |
|-------|------|-------------|
| `asset_sha256` | string (64-char hex) | Any operation on a specific asset |
| `manifest_sha256` | string (64-char hex) | After a manifest is written/read |
| `creator_id` | string | Register / verify operations |
| `chain_seq` | integer | Register — the sequence number assigned |
| `chain_prev` | string or null | Register — the prev hash linked |
| `license_spdx` | string | Register — the license recorded |
| `expected_sha256` | string | Verification failure — what the ledger expects |
| `actual_sha256` | string | Verification failure — what was computed |
| `git_commit` | string (40-char hex) | After a successful ledger commit |
| `watermark_stage` | integer 1–4 | Watermark embed / extract events |
| `watermark_key_id` | string | Watermark events — never the key itself |
| `recipient_id` | string | Stage 4 per-recipient watermark |
| `error` | string | ERROR records — exception class + message |
| `tb` | string | ERROR records (DEBUG level only) — truncated traceback |

### Named events

| `event` value | Level | Description |
|---------------|-------|-------------|
| `apv.register.start` | DEBUG | Command invoked for a given file |
| `apv.register.already_registered` | INFO | Asset hash found in vault; skipping |
| `apv.register.manifest_written` | INFO | Manifest written to `vault/manifests/` |
| `apv.register.ledger_committed` | INFO | `git commit` completed; hash recorded |
| `apv.verify.start` | DEBUG | Verify invoked |
| `apv.verify.ok` | INFO | Hash matches ledger; `VERIFIED` output |
| `apv.verify.tamper_detected` | WARNING | Hash mismatch — content changed after registration |
| `apv.verify.unregistered` | WARNING | No manifest found for this asset hash |
| `apv.verify.signature_invalid` | ERROR | Signed manifest fails Ed25519 verification (MVP+) |
| `apv.watermark.embed` | INFO | Watermark stage N embedded into asset |
| `apv.watermark.extract_ok` | INFO | Watermark payload extracted successfully |
| `apv.watermark.extract_failed` | WARNING | Extraction failed (expected for JPEG/transformed copies) |
| `apv.schema.invalid` | ERROR | Manifest fails schema validation on write |
| `apv.git.error` | ERROR | subprocess call to git returned non-zero |

## Log Levels

| Level | Use |
|-------|-----|
| `DEBUG` | Entry/exit of every command; intermediate hashing steps; git command lines (without secrets). Off in normal operation; enable with `APV_LOG_LEVEL=DEBUG`. |
| `INFO` | Successful operations: registration, verification pass, ledger commit. Always on. |
| `WARNING` | Expected anomalies that require human attention: tamper detected, watermark extraction failed on a transformed copy, unregistered asset. Always on. |
| `ERROR` | Unexpected failures: schema validation error on write, git subprocess failure, signature invalid. Always on. May indicate a bug or an attack. |

## `logs/` Directory Convention

The `logs/` directory is gitignored (except `.gitkeep`) and lives at the repo
root. In a production deployment it should be volume-mounted or forwarded to a
log aggregator.

```
logs/
  .gitkeep
  apv-YYYY-MM-DD.log   # Daily rotating NDJSON log; retention 90 days
  apv-error.log        # ERROR and above only; retention 365 days
```

Log rotation is handled by Python's `TimedRotatingFileHandler` with
`when="midnight"`, `backupCount=90`. The error log uses a
`MemoryHandler` flushing to `apv-error.log` when level >= ERROR.

In the PoC, logging defaults to stderr only (no file handler) unless
`APV_LOG_DIR` is set to a writable path. CI smoke runs without a log dir
to keep the environment clean.

## Key Metrics

These are the metrics APV should emit as log-derived counts or as Prometheus
counters (MVP/v1 when a hosted API arrives):

| Metric | Type | Description |
|--------|------|-------------|
| `apv_registrations_total` | Counter | Total successful manifest registrations |
| `apv_verifications_total{result}` | Counter | Labels: `ok`, `tamper_detected`, `unregistered` |
| `apv_signature_failures_total` | Counter | Ed25519 verification failures (security alert) |
| `apv_watermarks_embedded_total{stage}` | Counter | By stage (1–4) |
| `apv_watermarks_extracted_total{result}` | Counter | Labels: `ok`, `failed` |
| `apv_ledger_commit_duration_seconds` | Histogram | Wall time of `git commit` for a manifest |
| `apv_schema_validation_errors_total` | Counter | Should be zero in normal operation |

In the PoC these metrics exist only as counts derivable from log queries.
A Prometheus exporter is a v1 infrastructure task.

## Run Manifest Logging

When a batch operation processes multiple assets (e.g., a future
`register-batch` command), each run should emit a run-manifest record at the
start and end:

```json
{
  "ts": "2026-06-11T14:30:00.000Z",
  "level": "INFO",
  "event": "apv.run.start",
  "msg": "batch register starting",
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "asset_count": 42,
  "apv_version": "0.1.0"
}
```

```json
{
  "ts": "2026-06-11T14:30:05.321Z",
  "level": "INFO",
  "event": "apv.run.complete",
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "registered": 40,
  "skipped_existing": 2,
  "errors": 0,
  "duration_seconds": 5.321
}
```

The `run_id` (UUID4) lets log queries group all records from a single
invocation even across log rotation boundaries.

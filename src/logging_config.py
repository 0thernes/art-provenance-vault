"""Art Provenance Vault — structured JSON logger.

Provides a configured logger that emits NDJSON records matching the schema
defined in docs/OBSERVABILITY.md. Import and use get_logger() from any
provenance module.

Usage:
    from logging_config import get_logger
    log = get_logger(__name__)
    log.info("apv.register.manifest_written",
             asset_sha256="abc123...", manifest_sha256="def456...",
             creator_id="0_0@0thernes.art", chain_seq=1)

Environment variables:
    APV_LOG_LEVEL   DEBUG / INFO / WARNING / ERROR (default: INFO)
    APV_LOG_DIR     Directory for rotating log files. If unset, logs to stderr
                    only (suitable for CI and interactive use).
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Package-level constant — keep in sync with provenance.py
APV_VERSION = "0.1.0"


class _NdjsonFormatter(logging.Formatter):
    """Format a LogRecord as a single-line JSON object (NDJSON).

    The `event` field is taken from the first positional arg of the log call
    (e.g. ``log.info("apv.register.ok", asset_sha256=...)``). All keyword
    arguments passed via ``extra`` are included as top-level fields, making
    the schema in OBSERVABILITY.md directly expressible.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Core required fields (OBSERVABILITY.md)
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "event": record.getMessage(),
            "msg": record.getMessage(),
            "apv_version": APV_VERSION,
        }

        # Pull provenance-specific fields from record.__dict__ if present.
        _provenance_fields = (
            "asset_sha256",
            "manifest_sha256",
            "creator_id",
            "chain_seq",
            "chain_prev",
            "license_spdx",
            "expected_sha256",
            "actual_sha256",
            "git_commit",
            "watermark_stage",
            "watermark_key_id",
            "recipient_id",
            "run_id",
        )
        for field in _provenance_fields:
            value = record.__dict__.get(field)
            if value is not None:
                payload[field] = value

        # Include error info on ERROR records.
        if record.exc_info:
            payload["error"] = str(record.exc_info[1])
            # Truncated traceback at DEBUG level only to avoid log pollution.
            if record.levelno <= logging.DEBUG:
                import traceback

                payload["tb"] = "".join(
                    traceback.format_exception(*record.exc_info)
                )[-2000:]

        return json.dumps(payload, ensure_ascii=False)


def get_logger(name: str = "apv") -> logging.Logger:
    """Return a configured APV logger.

    Calling this multiple times with the same name returns the same logger
    (standard Python logging behaviour). The root APV logger is configured
    once; child loggers inherit the handlers.
    """
    root_name = "apv"
    root = logging.getLogger(root_name)

    if root.handlers:
        # Already configured — return child logger directly.
        return logging.getLogger(name)

    level_str = os.environ.get("APV_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_str, logging.INFO)
    root.setLevel(level)

    formatter = _NdjsonFormatter()

    # Always log to stderr.
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)
    root.addHandler(stderr_handler)

    # Optionally log to rotating daily files when APV_LOG_DIR is set.
    log_dir_env = os.environ.get("APV_LOG_DIR", "")
    if log_dir_env:
        log_dir = Path(log_dir_env)
        log_dir.mkdir(parents=True, exist_ok=True)

        # All-levels rotating log (90-day retention)
        all_handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(log_dir / "apv.log"),
            when="midnight",
            backupCount=90,
            encoding="utf-8",
        )
        all_handler.setFormatter(formatter)
        root.addHandler(all_handler)

        # ERROR-and-above log (365-day retention)
        error_handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(log_dir / "apv-error.log"),
            when="midnight",
            backupCount=365,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root.addHandler(error_handler)

    return logging.getLogger(name)

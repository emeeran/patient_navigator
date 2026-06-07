"""Structured logging configuration.

In production, emits JSON-formatted logs for machine parsing.
In development, keeps human-readable console output.
"""

import json
import logging
import sys
from datetime import UTC, datetime


class _JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Attach request_id from context var (set by RequestIdMiddleware)
        from app.middleware.request_id import request_id_ctx

        rid = request_id_ctx.get("")
        if rid:
            log_entry["request_id"] = rid

        # Include any extra fields the caller attached
        extra_keys = {"request_id", "request_id_ctx"}
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
                "taskName",
            } and key not in extra_keys:
                try:
                    json.dumps(value)  # ensure serialisable
                    log_entry[key] = value
                except (TypeError, ValueError):
                    log_entry[key] = str(value)

        if record.exc_info and record.exc_info[1] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


class _DevFormatter(logging.Formatter):
    """Human-readable formatter for development."""

    def format(self, record: logging.LogRecord) -> str:
        from app.middleware.request_id import request_id_ctx

        rid = request_id_ctx.get("")
        prefix = f"[{rid[:8]}] " if rid else ""
        base = super().format(record)
        return f"{prefix}{base}"


def setup_logging(*, environment: str = "development") -> None:
    """Configure root logger based on environment.

    Call once at application startup (in the lifespan handler).
    """
    root = logging.getLogger()

    # Avoid re-configuring (e.g., during tests with multiple lifespans)
    if root.handlers:
        return

    if environment == "production":
        formatter: logging.Formatter = _JsonFormatter()
    else:
        formatter = _DevFormatter(
            fmt="%(levelname)-8s %(name)s  %(message)s",
        )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root.addHandler(handler)
    root.setLevel(logging.INFO)

    # Quiet down noisy third-party loggers
    for noisy in ("uvicorn.error", "httpx", "httpcore", "aioredis"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # Keep uvicorn access log at INFO but through our formatter
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

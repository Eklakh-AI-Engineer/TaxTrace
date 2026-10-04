"""Structured logging configuration for TaxTrace.

Provides JSON-formatted logs with consistent fields for observability.
"""

from __future__ import annotations

import json
import logging
import sys
import traceback
from datetime import datetime, timezone
from typing import Any

from app.config import settings


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request context if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "tenant_id"):
            log_data["tenant_id"] = record.tenant_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "name", "pathname", "process", "processName",
                "relativeCreated", "thread", "threadName", "exc_info",
                "exc_text", "stack_info", "request_id", "tenant_id", "user_id"
            }:
                log_data[key] = value

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_data, default=str)


def setup_logging() -> None:
    """Configure application logging."""
    log_level = logging.DEBUG if settings.app_env == "development" else logging.INFO

    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)

    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if settings.app_env == "production":
        console_handler.setFormatter(JSONFormatter())
    else:
        # Human-readable format for development
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Set our app loggers to appropriate levels
    logging.getLogger("app").setLevel(log_level)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module."""
    return logging.getLogger(f"app.{name}")


class StructuredLogger:
    """Wrapper for structured logging with context."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def _log(self, level: int, message: str, **kwargs: Any) -> None:
        extra = {k: v for k, v in kwargs.items() if k not in ("exc_info", "stack_info")}
        self.logger.log(level, message, extra=extra, exc_info=kwargs.get("exc_info"))

    def debug(self, message: str, **kwargs: Any) -> None:
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        self._log(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        self._log(logging.ERROR, message, exc_info=True, **kwargs)

    def bind(self, **context: Any) -> "StructuredLogger":
        """Create a new logger with additional context."""
        # Create a new logger with context via adapter
        return ContextLogger(self.logger, context)


class ContextLogger(StructuredLogger):
    """Logger with persistent context."""

    def __init__(self, logger: logging.Logger, context: dict[str, Any]):
        super().__init__(logger)
        self.context = context

    def _log(self, level: int, message: str, **kwargs: Any) -> None:
        # Merge context with kwargs
        merged = {**self.context, **kwargs}
        extra = {k: v for k, v in merged.items() if k not in ("exc_info", "stack_info")}
        self.logger.log(level, message, extra=extra, exc_info=merged.get("exc_info"))

    def bind(self, **context: Any) -> "ContextLogger":
        """Create a new logger with additional context."""
        new_context = {**self.context, **context}
        return ContextLogger(self.logger, new_context)


# Initialize logging on import
setup_logging()
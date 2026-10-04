"""Prometheus metrics for TaxTrace observability.

Provides counters, histograms, and gauges for monitoring application health.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from functools import wraps
from typing import Callable, Any

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from app.config import settings

# Create a custom registry for our metrics
REGISTRY = CollectorRegistry()

# ---------------------------------------------------------------------------
# HTTP Request Metrics
# ---------------------------------------------------------------------------

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=REGISTRY,
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=REGISTRY,
)

HTTP_REQUEST_SIZE_BYTES = Histogram(
    "http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
    buckets=[100, 1000, 10000, 100000, 1000000, 10000000],
    registry=REGISTRY,
)

HTTP_RESPONSE_SIZE_BYTES = Histogram(
    "http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
    buckets=[100, 1000, 10000, 100000, 1000000, 10000000],
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Reconciliation Metrics
# ---------------------------------------------------------------------------

RECONCILIATION_RUNS_TOTAL = Counter(
    "reconciliation_runs_total",
    "Total number of reconciliation runs",
    ["status"],  # success, failure
    registry=REGISTRY,
)

RECONCILIATION_DURATION_SECONDS = Histogram(
    "reconciliation_duration_seconds",
    "Reconciliation job duration in seconds",
    buckets=[1, 5, 10, 30, 60, 120, 300, 600],
    registry=REGISTRY,
)

RECONCILIATION_EXCEPTIONS_TOTAL = Counter(
    "reconciliation_exceptions_total",
    "Total number of exceptions created during reconciliation",
    ["exception_type", "severity"],
    registry=REGISTRY,
)

RECONCILIATION_TRANSACTIONS_PROCESSED = Counter(
    "reconciliation_transactions_processed_total",
    "Total number of transactions processed in reconciliation",
    ["source"],  # book, portal
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# AI Metrics
# ---------------------------------------------------------------------------

AI_REQUESTS_TOTAL = Counter(
    "ai_requests_total",
    "Total number of AI provider requests",
    ["provider", "operation", "status"],  # success, failure, timeout
    registry=REGISTRY,
)

AI_TOKENS_USED = Counter(
    "ai_tokens_used_total",
    "Total number of tokens consumed",
    ["provider", "type"],  # input, output
    registry=REGISTRY,
)

AI_REQUEST_DURATION_SECONDS = Histogram(
    "ai_request_duration_seconds",
    "AI provider request duration in seconds",
    ["provider", "operation"],
    buckets=[0.5, 1, 2, 5, 10, 30, 60, 120],
    registry=REGISTRY,
)

AI_COST_USD = Counter(
    "ai_cost_usd_total",
    "Total AI provider cost in USD",
    ["provider"],
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Document Processing Metrics
# ---------------------------------------------------------------------------

DOCUMENT_UPLOADS_TOTAL = Counter(
    "document_uploads_total",
    "Total number of document uploads",
    ["document_type", "status"],  # success, failure, duplicate
    registry=REGISTRY,
)

DOCUMENT_PROCESSING_DURATION_SECONDS = Histogram(
    "document_processing_duration_seconds",
    "Document processing duration in seconds",
    ["document_type"],
    buckets=[0.5, 1, 2, 5, 10, 30, 60],
    registry=REGISTRY,
)

DOCUMENT_TRANSACTIONS_EXTRACTED = Counter(
    "document_transactions_extracted_total",
    "Total number of transactions extracted from documents",
    ["document_type"],
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Notice Processing Metrics
# ---------------------------------------------------------------------------

NOTICE_UPLOADS_TOTAL = Counter(
    "notice_uploads_total",
    "Total number of notice uploads",
    ["notice_type", "status"],
    registry=REGISTRY,
)

NOTICE_DRAFTS_GENERATED = Counter(
    "notice_drafts_generated_total",
    "Total number of notice drafts generated",
    ["notice_type", "status"],  # generated, approved, rejected
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Task Metrics
# ---------------------------------------------------------------------------

TASKS_CREATED_TOTAL = Counter(
    "tasks_created_total",
    "Total number of tasks created",
    ["source_type", "status"],
    registry=REGISTRY,
)

TASKS_COMPLETED_TOTAL = Counter(
    "tasks_completed_total",
    "Total number of tasks completed",
    ["source_type"],
    registry=REGISTRY,
)

TASKS_OVERDUE = Gauge(
    "tasks_overdue_count",
    "Number of overdue tasks",
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# System Metrics
# ---------------------------------------------------------------------------

ACTIVE_TENANTS = Gauge(
    "active_tenants_count",
    "Number of active tenants",
    registry=REGISTRY,
)

DB_CONNECTIONS_ACTIVE = Gauge(
    "db_connections_active",
    "Number of active database connections",
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Metrics Middleware
# ---------------------------------------------------------------------------

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP request metrics."""

    def __init__(self, app, excluded_paths: set[str] | None = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or {"/metrics", "/health", "/health/live", "/health/ready"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics collection for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        method = request.method
        path = request.url.path
        start_time = time.perf_counter()

        # Get request size
        content_length = request.headers.get("content-length")
        request_size = int(content_length) if content_length else 0

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            duration = time.perf_counter() - start_time

            # Record metrics
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=self._normalize_path(path),
                status_code=status_code,
            ).inc()

            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method,
                endpoint=self._normalize_path(path),
            ).observe(duration)

            if request_size:
                HTTP_REQUEST_SIZE_BYTES.labels(
                    method=method,
                    endpoint=self._normalize_path(path),
                ).observe(request_size)

        return response

    def _normalize_path(self, path: str) -> str:
        """Normalize path by replacing IDs with placeholders."""
        # Simple normalization: replace UUIDs and numeric IDs
        import re
        # Replace UUIDs
        path = re.sub(r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "/:id", path)
        # Replace numeric IDs
        path = re.sub(r"/\d+", "/:id", path)
        return path


# ---------------------------------------------------------------------------
# Metrics Endpoint
# ---------------------------------------------------------------------------

def metrics_endpoint() -> Response:
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST,
    )


# ---------------------------------------------------------------------------
# Helper Functions for Business Metrics
# ---------------------------------------------------------------------------

def record_reconciliation_run(status: str, duration: float, exception_counts: dict[str, dict[str, int]] | None = None) -> None:
    """Record metrics for a reconciliation run."""
    RECONCILIATION_RUNS_TOTAL.labels(status=status).inc()
    RECONCILIATION_DURATION_SECONDS.observe(duration)

    if exception_counts:
        for exc_type, severities in exception_counts.items():
            for severity, count in severities.items():
                RECONCILIATION_EXCEPTIONS_TOTAL.labels(
                    exception_type=exc_type,
                    severity=severity,
                ).inc(count)


def record_ai_request(provider: str, operation: str, status: str, duration: float, input_tokens: int = 0, output_tokens: int = 0, cost_usd: float = 0.0) -> None:
    """Record metrics for an AI provider request."""
    AI_REQUESTS_TOTAL.labels(provider=provider, operation=operation, status=status).inc()
    AI_REQUEST_DURATION_SECONDS.labels(provider=provider, operation=operation).observe(duration)

    if input_tokens:
        AI_TOKENS_USED.labels(provider=provider, type="input").inc(input_tokens)
    if output_tokens:
        AI_TOKENS_USED.labels(provider=provider, type="output").inc(output_tokens)
    if cost_usd:
        AI_COST_USD.labels(provider=provider).inc(cost_usd)


def record_document_upload(document_type: str, status: str, duration: float, transaction_count: int = 0) -> None:
    """Record metrics for a document upload."""
    DOCUMENT_UPLOADS_TOTAL.labels(document_type=document_type, status=status).inc()
    DOCUMENT_PROCESSING_DURATION_SECONDS.labels(document_type=document_type).observe(duration)
    if transaction_count:
        DOCUMENT_TRANSACTIONS_EXTRACTED.labels(document_type=document_type).inc(transaction_count)


def record_notice_draft(notice_type: str, status: str) -> None:
    """Record metrics for notice draft generation."""
    NOTICE_DRAFTS_GENERATED.labels(notice_type=notice_type, status=status).inc()


def record_task_event(source_type: str, event: str) -> None:
    """Record task lifecycle events."""
    if event == "created":
        TASKS_CREATED_TOTAL.labels(source_type=source_type, status="open").inc()
    elif event == "completed":
        TASKS_COMPLETED_TOTAL.labels(source_type=source_type).inc()


def update_overdue_tasks_count(count: int) -> None:
    """Update the overdue tasks gauge."""
    TASKS_OVERDUE.set(count)


def update_active_tenants_count(count: int) -> None:
    """Update the active tenants gauge."""
    ACTIVE_TENANTS.set(count)
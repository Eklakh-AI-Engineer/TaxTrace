"""Security hardening middleware for production deployment.

Implements:
- Security headers (CSP, HSTS, X-Frame-Options, etc.)
- Per-tenant rate limiting
- Request size limits
- Security audit logging
- CORS configuration
"""

from __future__ import annotations

import os
import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.auth import AuthContext, get_auth_context
from app.config import settings
from app.services import audit_service
from app.database import get_db


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    def __init__(self, app, *, hsts_max_age: int = 31536000, csp_policy: str | None = None):
        super().__init__(app)
        self.hsts_max_age = hsts_max_age
        self.csp_policy = csp_policy or (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # HSTS - only in production with HTTPS
        if settings.app_env == "production":
            response.headers["Strict-Transport-Security"] = f"max-age={self.hsts_max_age}; includeSubDomains; preload"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.csp_policy

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS protection (legacy but harmless)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy (feature policy)
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )

        # Remove server header
        if "Server" in response.headers:
            del response.headers["Server"]

        return response


class TenantRateLimitMiddleware(BaseHTTPMiddleware):
    """Per-tenant rate limiting with configurable limits."""

    def __init__(
        self,
        app,
        *,
        requests_per_minute: int = 200,
        requests_per_hour: int = 5000,
        burst_allowance: int = 50,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_allowance = burst_allowance
        self._minute_buckets: dict[str, list[float]] = {}
        self._hour_buckets: dict[str, list[float]] = {}

    def _get_tenant_key(self, request: Request) -> str:
        """Extract tenant identifier from request."""
        # Try to get from auth context
        if hasattr(request.state, "auth_context"):
            auth: AuthContext = request.state.auth_context
            return f"tenant:{auth.tenant_id}"
        # Fallback to IP
        forwarded = request.headers.get("X-Forwarded-For")
        ip = forwarded.split(",")[0].strip() if forwarded else request.client.host
        return f"ip:{ip}"

    def _cleanup_old_entries(self, bucket: list[float], window_seconds: int) -> list[float]:
        """Remove entries older than window."""
        now = time.time()
        return [ts for ts in bucket if now - ts < window_seconds]

    def _check_limit(self, bucket: list[float], limit: int, window_seconds: int) -> tuple[bool, int]:
        """Check if request is within limit. Returns (allowed, remaining)."""
        now = time.time()
        bucket[:] = self._cleanup_old_entries(bucket, window_seconds)
        if len(bucket) >= limit:
            return False, 0
        bucket.append(now)
        return True, limit - len(bucket)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        tenant_key = self._get_tenant_key(request)

        minute_bucket = self._minute_buckets.setdefault(f"{tenant_key}:min", [])
        hour_bucket = self._hour_buckets.setdefault(f"{tenant_key}:hour", [])

        minute_allowed, minute_remaining = self._check_limit(minute_bucket, self.requests_per_minute, 60)
        hour_allowed, hour_remaining = self._check_limit(hour_bucket, self.requests_per_hour, 3600)

        if not minute_allowed or not hour_allowed:
            # Log rate limit exceeded
            db_gen = get_db()
            db = next(db_gen)
            try:
                audit_service.log_event(
                    db,
                    auth=getattr(request.state, "auth_context", None),
                    entity_type="rate_limit",
                    entity_id=tenant_key,
                    event_type="rate_limit.exceeded",
                    payload={
                        "tenant_key": tenant_key,
                        "path": request.url.path,
                        "method": request.method,
                        "minute_remaining": minute_remaining,
                        "hour_remaining": hour_remaining,
                    },
                )
            finally:
                db.close()

            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please slow down.",
                        "retry_after_seconds": 60,
                    }
                },
                headers={
                    "X-RateLimit-Limit-Minute": str(self.requests_per_minute),
                    "X-RateLimit-Remaining-Minute": str(minute_remaining),
                    "X-RateLimit-Limit-Hour": str(self.requests_per_hour),
                    "X-RateLimit-Remaining-Hour": str(hour_remaining),
                },
            )

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(minute_remaining)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(hour_remaining)

        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Enforce request body size limits."""

    def __init__(self, app, *, max_size_bytes: int = 25 * 1024 * 1024):
        super().__init__(app)
        self.max_size_bytes = max_size_bytes

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        content_length = request.headers.get("Content-Length")
        if content_length and int(content_length) > self.max_size_bytes:
            return JSONResponse(
                status_code=413,
                content={
                    "error": {
                        "code": "PAYLOAD_TOO_LARGE",
                        "message": f"Request body exceeds maximum allowed size of {self.max_size_bytes // (1024*1024)}MB",
                    }
                },
            )
        return await call_next(request)


class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """Log security-relevant events."""

    SENSITIVE_PATHS = {
        "/api/v1/auth",
        "/api/v1/firms",
        "/api/v1/users",
        "/api/v1/documents",
        "/api/v1/reconciliations",
        "/api/v1/notices",
        "/api/v1/drafts",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        path = request.url.path

        # Check if this is a security-sensitive path
        is_sensitive = any(path.startswith(p) for p in self.SENSITIVE_PATHS)

        response = await call_next(request)

        duration_ms = int((time.time() - start_time) * 1000)

        # Log security events for sensitive paths
        if is_sensitive and hasattr(request.state, "auth_context"):
            auth: AuthContext = request.state.auth_context
            db_gen = get_db()
            db = next(db_gen)
            try:
                # Log authentication/authorization events
                if response.status_code in (401, 403, 429):
                    audit_service.log_event(
                        db,
                        auth=auth,
                        entity_type="security",
                        entity_id=auth.tenant_id,
                        event_type=f"security.http_{response.status_code}",
                        payload={
                            "path": path,
                            "method": request.method,
                            "status_code": response.status_code,
                            "duration_ms": duration_ms,
                            "user_agent": request.headers.get("User-Agent", "")[:200],
                            "ip": request.client.host if request.client else None,
                        },
                    )
                # Log successful sensitive operations
                elif response.status_code < 400 and request.method in ("POST", "PUT", "PATCH", "DELETE"):
                    audit_service.log_event(
                        db,
                        auth=auth,
                        entity_type="security",
                        entity_id=auth.tenant_id,
                        event_type="security.sensitive_operation",
                        payload={
                            "path": path,
                            "method": request.method,
                            "status_code": response.status_code,
                            "duration_ms": duration_ms,
                        },
                    )
            finally:
                db.close()

        return response


def setup_security_middleware(app: FastAPI) -> None:
    """Configure all security middleware for the FastAPI app.

    Order matters: middleware added last runs first (closest to the app).
    """
    # 1. CORS - should be early
    if settings.app_env == "production":
        # In production, restrict to known origins
        allowed_origins = settings.allowed_origins.split(",") if hasattr(settings, "allowed_origins") else []
    else:
        # In development, allow localhost
        allowed_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-*"],
        max_age=3600,
    )

    # 2. Request size limit (always enabled)
    app.add_middleware(RequestSizeLimitMiddleware, max_size_bytes=settings.max_upload_size_bytes)

    # 3. Security audit logging (only in production, or when explicitly enabled)
    if settings.app_env == "production" or os.getenv("ENABLE_SECURITY_AUDIT") == "true":
        app.add_middleware(SecurityAuditMiddleware)

    # 4. Per-tenant rate limiting (only in production)
    if settings.app_env == "production":
        app.add_middleware(TenantRateLimitMiddleware, requests_per_minute=200, requests_per_hour=5000)
    elif os.getenv("ENABLE_RATE_LIMIT") == "true":
        # Optional: enable in dev for testing
        app.add_middleware(TenantRateLimitMiddleware, requests_per_minute=1000, requests_per_hour=50000)

    # 5. Security headers (always enabled, with env-appropriate policy)
    if settings.app_env == "production":
        app.add_middleware(SecurityHeadersMiddleware)
    else:
        # In development, use relaxed CSP
        app.add_middleware(
            SecurityHeadersMiddleware,
            csp_policy=(
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' http://localhost:8000 ws://localhost:8000; "
                "frame-ancestors 'none';"
            ),
        )
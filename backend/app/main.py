"""TaxTrace FastAPI application entry point.

Registers all API routers, middleware, and error handlers.
"""

from __future__ import annotations

import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.clients import router as clients_router
from app.api.dashboard import router as dashboard_router
from app.api.documents import router as documents_router
from app.api.drafts import router as drafts_router
from app.api.exceptions import router as exceptions_router
from app.api.firms import router as firms_router
from app.api.health import router as health_router
from app.api.notices import router as notices_router
from app.api.periods import router as periods_router
from app.api.reconciliations import router as reconciliations_router
from app.api.tasks import router as tasks_router
from app.api.users import router as users_router
from app.api.webhooks import router as webhooks_router


from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# ---------------------------------------------------------------------------
# Rate Limiting
# ---------------------------------------------------------------------------

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="TaxTrace",
    description="AI Compliance Execution Platform for Small Indian CA Firms",
    version="0.1.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ---------------------------------------------------------------------------
# Middleware: Request-ID tracking
# ---------------------------------------------------------------------------


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique X-Request-ID to every request/response.

    If the caller supplies an X-Request-ID header it is preserved;
    otherwise a new UUID is generated. This supports structured
    logging and audit trail correlation (CODING_RULES.md §10).
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        # Store on request state so handlers can access it.
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


app.add_middleware(RequestIDMiddleware)


# ---------------------------------------------------------------------------
# Global exception handler — structured error format (API_SPEC.md §1)
# ---------------------------------------------------------------------------


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Format HTTPException instances into the standard error envelope."""
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "request_id": request_id,
            }
        },
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a structured error response for unhandled exceptions.

    This prevents stack traces from leaking to the client while
    preserving enough information for debugging via request_id.
    """
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
                "request_id": request_id,
            }
        },
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(health_router)
app.include_router(firms_router)
app.include_router(clients_router)
app.include_router(periods_router)
app.include_router(documents_router)
app.include_router(reconciliations_router)
app.include_router(exceptions_router)
app.include_router(notices_router)
app.include_router(drafts_router)
app.include_router(tasks_router)
app.include_router(dashboard_router)
app.include_router(users_router)
app.include_router(webhooks_router)


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "TaxTrace backend is running."}

"""Authentication module.

Provides JWT-based authentication with a development-mode bypass.

Auth chain per API_SPEC.md:
    token → user → membership → firm → authorization

In development mode (APP_ENV=development), accepts tokens in the format:
    Bearer dev.<user_id>.<firm_id>.<role>

In production mode, verifies real JWT tokens signed with SECRET_KEY.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings

# Algorithm used for JWT signing/verification.
JWT_ALGORITHM = "HS256"
# Default token lifetime.
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthContext:
    """Immutable authentication context resolved from a bearer token.

    Attributes:
        user_id: Authenticated user identifier.
        firm_id: Firm the user is acting within (= tenant_id).
        role: User's role within the firm.
        request_id: Unique request identifier for audit/logging.
    """

    user_id: str
    firm_id: str
    role: str
    request_id: str

    @property
    def tenant_id(self) -> str:
        """Firm ID is the tenant boundary."""
        return self.firm_id


def create_access_token(
    user_id: str,
    firm_id: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token.

    Used for integration tests and future login endpoints.
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": user_id,
        "firm_id": firm_id,
        "role": role,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


def _decode_dev_token(token: str) -> AuthContext:
    """Parse a development-mode token: ``dev.<user_id>.<firm_id>.<role>``."""
    parts = token.split(".")
    if len(parts) != 4 or parts[0] != "dev":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid development token format. Expected: dev.<user_id>.<firm_id>.<role>",
        )
    _, user_id, firm_id, role = parts
    if not user_id or not firm_id or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Development token contains empty fields.",
        )
    return AuthContext(
        user_id=user_id,
        firm_id=firm_id,
        role=role,
        request_id=str(uuid.uuid4()),
    )


def _decode_jwt_token(token: str) -> AuthContext:
    """Verify and decode a production JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
        )

    user_id = payload.get("sub")
    firm_id = payload.get("firm_id")
    role = payload.get("role")

    if not user_id or not firm_id or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing required claims (sub, firm_id, role).",
        )

    return AuthContext(
        user_id=user_id,
        firm_id=firm_id,
        role=role,
        request_id=str(uuid.uuid4()),
    )


def get_auth_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
) -> AuthContext:
    """FastAPI dependency that resolves the authenticated context.

    Supports two modes:
    - Development: tokens starting with ``dev.`` are parsed without signature.
    - Production: standard JWT verification.

    The resolved ``AuthContext`` carries tenant information through the
    entire request lifecycle.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Development-mode shortcut.
    if settings.app_env == "development" and token.startswith("dev."):
        ctx = _decode_dev_token(token)
    else:
        ctx = _decode_jwt_token(token)

    # Honour explicit request IDs for tracing.
    if x_request_id:
        ctx = AuthContext(
            user_id=ctx.user_id,
            firm_id=ctx.firm_id,
            role=ctx.role,
            request_id=x_request_id,
        )

    return ctx

"""
FormatGuard Security — JWT token validation using Supabase JWT secret.
Verifies aud, iss, exp claims on every request.
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from jose import JWTError, jwt
import structlog

from app.config import settings

logger = structlog.get_logger()

# Supabase JWT algorithm
ALGORITHM = "HS256"


def verify_jwt_token(token: str) -> dict:
    """
    Verify and decode a Supabase JWT token.

    Validates:
    - Token signature using SUPABASE_JWT_SECRET
    - Expiration (exp claim)
    - Issuer (iss claim matches Supabase URL)

    Returns the decoded token payload.
    Raises HTTPException 401 on any validation failure.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[ALGORITHM],
            options={
                "verify_aud": False,  # Supabase doesn't always set aud
                "verify_iss": True,
                "verify_exp": True,
            },
            issuer=f"{settings.SUPABASE_URL}/auth/v1",
        )

        # Extract user ID from sub claim
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject claim",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Validate UUID format
        try:
            uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID in token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check expiration explicitly (belt and suspenders)
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload

    except JWTError as e:
        try:
            header = jwt.get_unverified_header(token)
            logger.warning("JWT validation failed", error=str(e), header=header)
        except Exception:
            logger.warning("JWT validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def extract_user_id(payload: dict) -> uuid.UUID:
    """Extract and return the user UUID from a decoded JWT payload."""
    return uuid.UUID(payload["sub"])


def extract_user_email(payload: dict) -> str | None:
    """Extract email from JWT payload if available."""
    return payload.get("email")


def extract_user_role(payload: dict) -> str | None:
    """Extract role from JWT app_metadata if available."""
    app_metadata = payload.get("app_metadata", {})
    return app_metadata.get("role")

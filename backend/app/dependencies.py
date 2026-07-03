"""
FormatGuard Dependencies — FastAPI dependency injection functions.
Provides current user extraction, quota checking, and database sessions.
"""

import uuid
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import QuotaExceededError, RateLimitExceededError
from app.core.security import extract_user_id, verify_jwt_token
from app.database import get_db
from app.models.user import User

# Bearer token extraction
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract and validate the current user from JWT bearer token.
    Creates user record on first login (Supabase handles registration).
    """
    payload = verify_jwt_token(credentials.credentials)
    user_id = extract_user_id(payload)

    # Look up user in database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        # Auto-create user on first API call (Supabase handles auth registration)
        user = User(
            id=user_id,
            email=payload.get("email", "unknown@example.com"),
            full_name=payload.get("user_metadata", {}).get("full_name", "New User"),
            role=payload.get("app_metadata", {}).get("role", "student"),
        )
        db.add(user)
        await db.flush()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require institutional_admin or super_admin role."""
    if current_user.role not in ("institutional_admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def require_super_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require super_admin role."""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    return current_user


async def check_submission_quota(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Check if user has remaining submission quota.

    Free tier: max 5 checks/month
    Student Pro: unlimited (-1)
    Institutional: enforced per institution seat count

    Raises HTTP 402 if quota exceeded with upgrade info.
    """
    # Determine the limit based on subscription tier
    tier_limits = {
        "free": settings.FREE_TIER_MONTHLY_CHECKS,
        "student_pro": settings.STUDENT_PRO_MONTHLY_CHECKS,
        "institutional_starter": 100,
        "institutional_growth": 500,
        "enterprise": -1,  # unlimited
    }

    limit = tier_limits.get(current_user.subscription_tier, settings.FREE_TIER_MONTHLY_CHECKS)

    # -1 means unlimited
    if limit == -1:
        return current_user

    # Check if we need to reset the monthly counter
    now = datetime.now(timezone.utc)
    if current_user.monthly_checks_reset_at is None or current_user.monthly_checks_reset_at <= now:
        # Reset counter — set next reset to first of next month
        current_user.monthly_checks_used = 0
        if now.month == 12:
            next_reset = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            next_reset = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
        current_user.monthly_checks_reset_at = next_reset
        await db.flush()

    # Check quota
    if current_user.monthly_checks_used >= limit:
        raise QuotaExceededError(tier=current_user.subscription_tier, limit=limit)

    return current_user

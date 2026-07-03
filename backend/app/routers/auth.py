"""
Auth Router — Authentication endpoints for user profile and token verification.
Actual authentication (login/register) is handled by Supabase on the frontend.
This router handles backend-side user profile management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserProfile, UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserProfile)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    """Get the current authenticated user's profile."""
    return UserProfile(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        subscription_tier=current_user.subscription_tier,
        institution_id=str(current_user.institution_id) if current_user.institution_id else None,
        monthly_checks_used=current_user.monthly_checks_used,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
    )


@router.put("/me", response_model=UserProfile)
async def update_my_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's profile (full name only)."""
    if data.full_name:
        current_user.full_name = data.full_name
        await db.flush()

    return UserProfile(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        subscription_tier=current_user.subscription_tier,
        institution_id=str(current_user.institution_id) if current_user.institution_id else None,
        monthly_checks_used=current_user.monthly_checks_used,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
    )


@router.get("/verify")
async def verify_token(
    current_user: User = Depends(get_current_user),
):
    """Verify that the current JWT token is valid. Returns 200 if valid, 401 if not."""
    return {
        "valid": True,
        "user_id": str(current_user.id),
        "role": current_user.role,
    }

"""
User Pydantic Schemas — request/response models for user endpoints.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserProfile(BaseModel):
    """User profile response."""
    id: str
    email: str
    full_name: str
    role: str
    subscription_tier: str
    institution_id: Optional[str] = None
    monthly_checks_used: int = 0
    is_active: bool = True
    created_at: str

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """User profile update request."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)


class UserRoleUpdate(BaseModel):
    """Admin endpoint for updating user roles."""
    role: str = Field(
        ...,
        pattern="^(student|faculty|institutional_admin|super_admin)$",
        description="User role"
    )

"""
Ruleset Pydantic Schemas — request/response models for ruleset endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any


class RulesetCreate(BaseModel):
    """Create a new ruleset."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: bool = False
    rules: dict = Field(..., description="Ruleset JSON schema following FormatGuard format")


class RulesetUpdate(BaseModel):
    """Update an existing ruleset (creates new version)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: Optional[bool] = None
    rules: Optional[dict] = None
    change_log: Optional[str] = None


class RulesetResponse(BaseModel):
    """Ruleset response model."""
    id: str
    name: str
    description: Optional[str] = None
    institution_id: Optional[str] = None
    created_by: Optional[str] = None
    version: str = "1.0"
    is_public: bool = False
    is_verified: bool = False
    download_count: int = 0
    rating_avg: Optional[float] = None
    rules: dict
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class RulesetList(BaseModel):
    """Paginated list of rulesets."""
    rulesets: list[RulesetResponse]
    total: int
    page: int
    limit: int


class RulesetRatingCreate(BaseModel):
    """Rate a marketplace ruleset."""
    rating: int = Field(..., ge=1, le=5, description="1-5 star rating")
    review: Optional[str] = None


class MarketplaceQuery(BaseModel):
    """Query parameters for marketplace search."""
    search: Optional[str] = None
    institution: Optional[str] = None
    sort_by: str = Field(default="download_count", pattern="^(download_count|rating_avg|created_at|name)$")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)

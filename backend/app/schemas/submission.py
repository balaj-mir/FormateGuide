"""
Submission Pydantic Schemas — request/response models for submission endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional


class SubmissionCreate(BaseModel):
    """Upload submission request (file handled separately via multipart)."""
    ruleset_id: str = Field(..., description="UUID of the ruleset to check against")


class SubmissionResponse(BaseModel):
    """Submission response model."""
    id: str
    user_id: str
    ruleset_id: Optional[str] = None
    ruleset_version: Optional[str] = None
    original_filename: Optional[str] = None
    file_size_bytes: Optional[int] = None
    file_type: str = "docx"
    status: str = "pending"
    error_message: Optional[str] = None
    processing_started_at: Optional[str] = None
    processing_completed_at: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class SubmissionList(BaseModel):
    """Paginated list of submissions."""
    submissions: list[SubmissionResponse]
    total: int
    page: int
    limit: int
    has_more: bool


class SubmissionStatus(BaseModel):
    """Real-time submission processing status."""
    id: str
    status: str
    progress_step: Optional[str] = None
    error_message: Optional[str] = None

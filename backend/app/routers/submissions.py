"""
Submissions Router — Upload documents, list submissions, check status via SSE.
"""

import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.dependencies import check_submission_quota, get_current_user
from app.core.exceptions import FileValidationError
from app.models.submission import Submission
from app.models.ruleset import Ruleset
from app.models.user import User
from app.schemas.submission import SubmissionList, SubmissionResponse
from app.services.storage_service import upload_document, delete_document
from app.tasks.processing_tasks import process_submission
import structlog

logger = structlog.get_logger()
router = APIRouter()

ALLOWED_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_FILE_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # Convert to bytes


@router.post("/upload", response_model=SubmissionResponse, status_code=201)
async def upload_submission(
    file: UploadFile = File(...),
    ruleset_id: str = Form(...),
    current_user: User = Depends(check_submission_quota),
    db: AsyncSession = Depends(get_db),
):
    """Upload .docx, create submission, queue processing."""
    # Validate file type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise FileValidationError(
            f"Invalid file type: {file.content_type}. Only .docx files are accepted."
        )

    # Read file bytes
    file_bytes = await file.read()

    # Validate file size
    if len(file_bytes) > MAX_FILE_SIZE:
        raise FileValidationError(
            f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit. Your file is {len(file_bytes) / (1024*1024):.1f}MB."
        )

    # Validate ZIP structure (basic .docx check)
    if file_bytes[:4] != b'PK\x03\x04':
        raise FileValidationError("File is not a valid .docx document (invalid ZIP structure).")

    # Verify ruleset exists
    ruleset_uuid = uuid.UUID(ruleset_id)
    result = await db.execute(select(Ruleset).where(Ruleset.id == ruleset_uuid))
    ruleset = result.scalar_one_or_none()
    if not ruleset:
        raise HTTPException(status_code=404, detail="Ruleset not found")

    # Create submission record
    submission = Submission(
        user_id=current_user.id,
        ruleset_id=ruleset.id,
        ruleset_version=ruleset.version,
        original_filename=file.filename,
        file_size_bytes=len(file_bytes),
        file_type="docx",
        status="pending",
    )
    db.add(submission)
    await db.flush()

    # Upload to S3/R2
    try:
        file_key = await upload_document(file_bytes, current_user.id, submission.id)
        submission.file_key = file_key
    except Exception as e:
        logger.error("S3 upload failed", error=str(e))
        submission.status = "failed"
        submission.error_message = "Failed to upload file to storage"
        await db.flush()
        raise HTTPException(status_code=503, detail="File storage service unavailable")

    # Increment monthly check counter
    current_user.monthly_checks_used += 1
    await db.flush()

    # Queue processing task
    try:
        process_submission.delay(str(submission.id))
        logger.info("Submission queued", submission_id=str(submission.id))
    except Exception as e:
        logger.error("Failed to queue task", error=str(e))
        submission.status = "failed"
        submission.error_message = "Failed to queue document for processing"

    return SubmissionResponse(
        id=str(submission.id),
        user_id=str(submission.user_id),
        ruleset_id=str(submission.ruleset_id),
        ruleset_version=submission.ruleset_version,
        original_filename=submission.original_filename,
        file_size_bytes=submission.file_size_bytes,
        file_type=submission.file_type,
        status=submission.status,
        created_at=submission.created_at.isoformat(),
    )


@router.get("", response_model=SubmissionList)
async def list_submissions(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's submissions (paginated)."""
    offset = (page - 1) * limit

    # Count total
    count_result = await db.execute(
        select(func.count(Submission.id)).where(Submission.user_id == current_user.id)
    )
    total = count_result.scalar() or 0

    # Fetch submissions
    result = await db.execute(
        select(Submission)
        .where(Submission.user_id == current_user.id)
        .order_by(Submission.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    submissions = result.scalars().all()

    return SubmissionList(
        submissions=[
            SubmissionResponse(
                id=str(s.id), user_id=str(s.user_id),
                ruleset_id=str(s.ruleset_id) if s.ruleset_id else None,
                ruleset_version=s.ruleset_version,
                original_filename=s.original_filename,
                file_size_bytes=s.file_size_bytes,
                file_type=s.file_type, status=s.status,
                error_message=s.error_message,
                processing_started_at=s.processing_started_at.isoformat() if s.processing_started_at else None,
                processing_completed_at=s.processing_completed_at.isoformat() if s.processing_completed_at else None,
                created_at=s.created_at.isoformat(),
            )
            for s in submissions
        ],
        total=total, page=page, limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get("/{submission_id}", response_model=SubmissionResponse)
async def get_submission(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get submission details."""
    sid = uuid.UUID(submission_id)
    result = await db.execute(
        select(Submission).where(Submission.id == sid, Submission.user_id == current_user.id)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    return SubmissionResponse(
        id=str(submission.id), user_id=str(submission.user_id),
        ruleset_id=str(submission.ruleset_id) if submission.ruleset_id else None,
        ruleset_version=submission.ruleset_version,
        original_filename=submission.original_filename,
        file_size_bytes=submission.file_size_bytes,
        file_type=submission.file_type, status=submission.status,
        error_message=submission.error_message,
        processing_started_at=submission.processing_started_at.isoformat() if submission.processing_started_at else None,
        processing_completed_at=submission.processing_completed_at.isoformat() if submission.processing_completed_at else None,
        created_at=submission.created_at.isoformat(),
    )


@router.delete("/{submission_id}", status_code=204)
async def delete_submission(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete submission and associated files from S3."""
    sid = uuid.UUID(submission_id)
    result = await db.execute(
        select(Submission).where(Submission.id == sid, Submission.user_id == current_user.id)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Delete from S3
    if submission.file_key:
        try:
            await delete_document(submission.file_key)
        except Exception as e:
            logger.warning("Failed to delete S3 file", error=str(e))

    await db.delete(submission)


@router.get("/{submission_id}/status")
async def stream_submission_status(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """SSE endpoint for real-time processing status updates."""
    sid = uuid.UUID(submission_id)

    async def generate():
        for _ in range(300):  # Max 5 minutes
            async with db.begin():
                result = await db.execute(
                    select(Submission).where(Submission.id == sid)
                )
                submission = result.scalar_one_or_none()

            if not submission:
                yield f"data: {{\"status\": \"not_found\"}}\n\n"
                break

            yield f"data: {{\"status\": \"{submission.status}\", \"error\": \"{submission.error_message or ''}\"}}\n\n"

            if submission.status in ("complete", "failed"):
                break

            await asyncio.sleep(1)

    return StreamingResponse(generate(), media_type="text/event-stream")

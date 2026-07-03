"""
Corrections Router — Apply corrections and download corrected documents.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.submission import Submission
from app.models.report import ComplianceReport
from app.models.violation import Violation
from app.models.user import User
from app.schemas.report import CorrectionRequest
from app.services.correction_engine import apply_corrections
from app.services.storage_service import (
    download_document, upload_corrected_doc, generate_signed_url,
)
import structlog

logger = structlog.get_logger()
router = APIRouter()


async def _get_submission_with_report(submission_id: str, user: User, db: AsyncSession):
    """Helper to get submission and verify ownership."""
    sid = uuid.UUID(submission_id)
    result = await db.execute(
        select(Submission).where(Submission.id == sid, Submission.user_id == user.id)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if submission.status != "complete":
        raise HTTPException(status_code=400, detail="Submission processing not yet complete")

    report_result = await db.execute(
        select(ComplianceReport)
        .options(selectinload(ComplianceReport.violations))
        .where(ComplianceReport.submission_id == sid)
    )
    report = report_result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return submission, report


@router.post("/{submission_id}/apply")
async def apply_selected_corrections(
    submission_id: str,
    request: CorrectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Apply selected corrections to the document."""
    submission, report = await _get_submission_with_report(submission_id, current_user, db)

    # Download original document
    file_bytes = await download_document(submission.file_key)

    # Build violations list from DB
    violations_data = [
        {"id": str(v.id), "element_type": v.element_type, "rule_name": v.rule_name,
         "expected_value": v.expected_value, "is_auto_fixable": v.is_auto_fixable,
         "severity": v.severity}
        for v in report.violations
    ]

    # Apply corrections
    corrected_bytes = apply_corrections(file_bytes, violations_data, request.violation_ids or [])

    # Upload corrected document
    corrected_key = await upload_corrected_doc(corrected_bytes, current_user.id, submission.id)
    report.corrected_doc_key = corrected_key

    # Mark violations as fixed
    for v in report.violations:
        if not request.violation_ids or str(v.id) in request.violation_ids:
            if v.is_auto_fixable:
                v.fix_applied = True

    await db.flush()
    return {"message": "Corrections applied", "corrected_doc_key": corrected_key}


@router.post("/{submission_id}/apply-all-critical")
async def apply_all_critical(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Apply all critical auto-fixable corrections."""
    submission, report = await _get_submission_with_report(submission_id, current_user, db)

    critical_ids = [str(v.id) for v in report.violations if v.severity == "critical" and v.is_auto_fixable]
    if not critical_ids:
        return {"message": "No critical auto-fixable violations found"}

    file_bytes = await download_document(submission.file_key)
    violations_data = [
        {"id": str(v.id), "element_type": v.element_type, "rule_name": v.rule_name,
         "expected_value": v.expected_value, "is_auto_fixable": True, "severity": "critical"}
        for v in report.violations if str(v.id) in critical_ids
    ]

    corrected_bytes = apply_corrections(file_bytes, violations_data, critical_ids)
    corrected_key = await upload_corrected_doc(corrected_bytes, current_user.id, submission.id)
    report.corrected_doc_key = corrected_key

    for v in report.violations:
        if str(v.id) in critical_ids:
            v.fix_applied = True

    await db.flush()
    return {"message": f"{len(critical_ids)} critical fixes applied", "corrected_doc_key": corrected_key}


@router.get("/{submission_id}/download")
async def download_corrected(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download corrected .docx via signed URL."""
    submission, report = await _get_submission_with_report(submission_id, current_user, db)
    if not report.corrected_doc_key:
        raise HTTPException(status_code=404, detail="No corrected document available. Apply corrections first.")

    url = await generate_signed_url(report.corrected_doc_key)
    return {"url": url}

"""
Reports Router — Get compliance reports and PDF downloads.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.report import ComplianceReport
from app.models.submission import Submission
from app.models.violation import Violation
from app.models.user import User
from app.schemas.report import ComplianceReportResponse, DocumentMetadata, ReportSummary, ViolationResponse
from app.services.storage_service import generate_signed_url

router = APIRouter()


@router.get("/{submission_id}", response_model=ComplianceReportResponse)
async def get_report(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full compliance report with all violations."""
    sid = uuid.UUID(submission_id)

    # Verify submission belongs to user
    sub_result = await db.execute(
        select(Submission).where(Submission.id == sid, Submission.user_id == current_user.id)
    )
    submission = sub_result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Get report with violations
    result = await db.execute(
        select(ComplianceReport)
        .options(selectinload(ComplianceReport.violations))
        .where(ComplianceReport.submission_id == sid)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not yet available")

    # Generate signed URLs
    pdf_url = None
    corrected_url = None
    if report.report_pdf_key:
        try:
            pdf_url = await generate_signed_url(report.report_pdf_key)
        except Exception:
            pass
    if report.corrected_doc_key:
        try:
            corrected_url = await generate_signed_url(report.corrected_doc_key)
        except Exception:
            pass

    doc_meta = None
    if report.document_metadata:
        doc_meta = DocumentMetadata(
            page_count=report.document_metadata.get("page_count", 0),
            word_count=report.document_metadata.get("word_count", 0),
            detected_sections=report.document_metadata.get("detected_sections", []),
        )

    return ComplianceReportResponse(
        id=str(report.id),
        submission_id=str(report.submission_id),
        compliance_score=float(report.compliance_score) if report.compliance_score else 0.0,
        total_violations=report.total_violations,
        critical_count=report.critical_count,
        warning_count=report.warning_count,
        suggestion_count=report.suggestion_count,
        estimated_fix_time_minutes=report.estimated_fix_time_minutes,
        total_elements_checked=report.total_elements_checked,
        violations=[
            ViolationResponse(
                id=str(v.id), page_number=v.page_number, section_name=v.section_name,
                element_type=v.element_type, rule_name=v.rule_name,
                current_value=v.current_value, expected_value=v.expected_value,
                severity=v.severity, is_auto_fixable=v.is_auto_fixable,
                is_ai_detected=v.is_ai_detected, context_excerpt=v.context_excerpt,
                affected_count=v.affected_count, fix_applied=v.fix_applied,
            )
            for v in sorted(report.violations, key=lambda x: x.display_order or 0)
        ],
        document_metadata=doc_meta,
        report_pdf_url=pdf_url,
        corrected_doc_url=corrected_url,
        created_at=report.created_at.isoformat(),
    )


@router.get("/{submission_id}/pdf")
async def get_report_pdf_url(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get signed URL for compliance report PDF download."""
    sid = uuid.UUID(submission_id)
    sub_result = await db.execute(
        select(Submission).where(Submission.id == sid, Submission.user_id == current_user.id)
    )
    if not sub_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Submission not found")

    result = await db.execute(
        select(ComplianceReport).where(ComplianceReport.submission_id == sid)
    )
    report = result.scalar_one_or_none()
    if not report or not report.report_pdf_key:
        raise HTTPException(status_code=404, detail="Report PDF not available")

    url = await generate_signed_url(report.report_pdf_key)
    return {"url": url}


@router.get("/{submission_id}/summary", response_model=ReportSummary)
async def get_report_summary(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get summary stats only (no violations list)."""
    sid = uuid.UUID(submission_id)
    sub_result = await db.execute(
        select(Submission).where(Submission.id == sid, Submission.user_id == current_user.id)
    )
    if not sub_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Submission not found")

    result = await db.execute(
        select(ComplianceReport).where(ComplianceReport.submission_id == sid)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not yet available")

    return ReportSummary(
        submission_id=str(report.submission_id),
        compliance_score=float(report.compliance_score) if report.compliance_score else 0.0,
        total_violations=report.total_violations,
        critical_count=report.critical_count,
        warning_count=report.warning_count,
        suggestion_count=report.suggestion_count,
        estimated_fix_time_minutes=report.estimated_fix_time_minutes,
    )

"""
Processing Tasks — Celery async tasks for document processing pipeline.
Full 10-step pipeline: download → parse → check → AI → report → save.
"""

from celery import shared_task
from datetime import datetime, timezone
import structlog

logger = structlog.get_logger()


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="process_submission",
)
def process_submission(self, submission_id: str):
    """
    Main processing task. Pipeline:
    1. Update status to 'processing'
    2. Download .docx from S3/R2
    3. Parse document → StructuredDocumentObject
    4. Run compliance engine → violations list
    5. Run AI service → AI violations (if enabled)
    6. Merge violations, calculate compliance score
    7. Generate compliance report PDF
    8. Save report PDF to S3/R2
    9. Save ComplianceReport + Violations to PostgreSQL
    10. Update status to 'complete'
    """
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session, sessionmaker
    from app.config import settings
    from app.models.submission import Submission
    from app.models.report import ComplianceReport
    from app.models.violation import Violation as ViolationModel
    from app.models.ruleset import Ruleset
    from app.services.document_parser import parse_docx
    from app.services.compliance_engine import run_compliance_check

    # Use sync engine for Celery (Celery doesn't support async)
    sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(sync_url)
    SessionLocal = sessionmaker(bind=engine)

    session = SessionLocal()

    try:
        # Step 1: Get submission and update status
        submission = session.execute(
            select(Submission).where(Submission.id == submission_id)
        ).scalar_one_or_none()

        if not submission:
            logger.error("Submission not found", submission_id=submission_id)
            return

        submission.status = "processing"
        submission.processing_started_at = datetime.now(timezone.utc)
        session.commit()
        logger.info("Processing started", submission_id=submission_id)

        # Step 2: Download document from S3
        from app.services.storage_service import s3_client, BUCKET
        try:
            response = s3_client.get_object(Bucket=BUCKET, Key=submission.file_key)
            file_bytes = response["Body"].read()
        except Exception as e:
            logger.error("Failed to download from S3", error=str(e))
            submission.status = "failed"
            submission.error_message = f"Failed to download file: {str(e)}"
            session.commit()
            return

        # Step 3: Parse document
        try:
            doc = parse_docx(file_bytes, submission.original_filename or "document.docx")
            logger.info("Document parsed", paragraphs=doc.paragraph_count, pages=doc.page_count)
        except ValueError as e:
            submission.status = "failed"
            submission.error_message = f"Document parsing failed: {str(e)}"
            session.commit()
            return

        # Step 4: Get ruleset and run compliance check
        ruleset = session.execute(
            select(Ruleset).where(Ruleset.id == submission.ruleset_id)
        ).scalar_one_or_none()

        if not ruleset:
            submission.status = "failed"
            submission.error_message = "Ruleset not found"
            session.commit()
            return

        violations, compliance_score = run_compliance_check(doc, ruleset.rules)
        logger.info("Compliance check complete", violations=len(violations), score=compliance_score)

        # Step 5-6: AI checks skipped for now (requires async + API key)

        # Step 7-8: Report PDF generation (simplified for now)
        report_pdf_key = None
        try:
            from app.services.report_generator import generate_report_pdf
            pdf_bytes = generate_report_pdf(
                filename=submission.original_filename or "document.docx",
                compliance_score=compliance_score,
                violations=violations,
                ruleset_name=ruleset.name,
                ruleset_version=ruleset.version,
                doc_metadata={
                    "page_count": doc.page_count,
                    "word_count": doc.word_count,
                    "detected_sections": doc.detected_sections,
                },
            )
            if pdf_bytes:
                report_pdf_key = f"reports/{submission.user_id}/{submission.id}/compliance_report.pdf"
                s3_client.put_object(
                    Bucket=BUCKET, Key=report_pdf_key,
                    Body=pdf_bytes, ContentType="application/pdf"
                )
                logger.info("Report PDF uploaded", key=report_pdf_key)
        except Exception as e:
            logger.warning("PDF generation failed, continuing", error=str(e))

        # Step 9: Save report + violations to database
        critical_count = sum(1 for v in violations if v.severity == "critical")
        warning_count = sum(1 for v in violations if v.severity == "warning")
        suggestion_count = sum(1 for v in violations if v.severity == "suggestion")

        # Estimate fix time: 1 min per critical, 0.5 min per warning
        fix_time = critical_count * 1 + warning_count * 0.5

        report = ComplianceReport(
            submission_id=submission.id,
            compliance_score=compliance_score,
            total_violations=len(violations),
            critical_count=critical_count,
            warning_count=warning_count,
            suggestion_count=suggestion_count,
            estimated_fix_time_minutes=int(fix_time) or 1,
            total_elements_checked=len(violations) + int(compliance_score / 100 * len(violations)) if compliance_score < 100 else max(len(doc.paragraphs), 1),
            report_pdf_key=report_pdf_key,
            document_metadata={
                "page_count": doc.page_count,
                "word_count": doc.word_count,
                "detected_sections": doc.detected_sections,
            },
        )
        session.add(report)
        session.flush()

        # Save individual violations
        for i, v in enumerate(violations):
            violation = ViolationModel(
                report_id=report.id,
                page_number=v.page_number,
                section_name=v.section_name,
                element_type=v.element_type,
                rule_name=v.rule_name,
                current_value=v.current_value,
                expected_value=v.expected_value,
                severity=v.severity,
                is_auto_fixable=v.is_auto_fixable,
                is_ai_detected=v.is_ai_detected,
                context_excerpt=v.context_excerpt,
                affected_count=v.affected_count,
                display_order=i + 1,
            )
            session.add(violation)

        # Step 10: Update submission status
        submission.status = "complete"
        submission.processing_completed_at = datetime.now(timezone.utc)
        session.commit()

        logger.info(
            "Processing complete",
            submission_id=submission_id,
            score=compliance_score,
            violations=len(violations),
        )

    except Exception as e:
        logger.error("Processing failed", submission_id=submission_id, error=str(e))
        session.rollback()
        try:
            submission.status = "failed"
            submission.error_message = f"Processing error: {str(e)}"
            session.commit()
        except Exception:
            pass
        raise
    finally:
        session.close()

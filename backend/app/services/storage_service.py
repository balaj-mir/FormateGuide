"""
Storage Service — All file operations for S3/Cloudflare R2.
Handles document upload, download, signed URL generation, and deletion.

File key naming convention:
  documents/{user_id}/{submission_id}/original.docx
  documents/{user_id}/{submission_id}/corrected.docx
  reports/{user_id}/{submission_id}/compliance_report.pdf
"""

import uuid
from datetime import datetime, timezone

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
import structlog

from app.config import settings

logger = structlog.get_logger()

# S3/R2 client with custom endpoint for Cloudflare R2
s3_client = boto3.client(
    "s3",
    endpoint_url=settings.S3_ENDPOINT_URL,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    config=BotoConfig(
        signature_version="s3v4",
        retries={"max_attempts": 3, "mode": "standard"},
    ),
)

BUCKET = settings.S3_BUCKET_NAME


def _build_document_key(user_id: uuid.UUID, submission_id: uuid.UUID) -> str:
    """Build the S3 key for an original document."""
    return f"documents/{user_id}/{submission_id}/original.docx"


def _build_corrected_key(user_id: uuid.UUID, submission_id: uuid.UUID) -> str:
    """Build the S3 key for a corrected document."""
    return f"documents/{user_id}/{submission_id}/corrected.docx"


def _build_report_key(user_id: uuid.UUID, submission_id: uuid.UUID) -> str:
    """Build the S3 key for a compliance report PDF."""
    return f"reports/{user_id}/{submission_id}/compliance_report.pdf"


async def upload_document(
    file_bytes: bytes,
    user_id: uuid.UUID,
    submission_id: uuid.UUID,
) -> str:
    """
    Upload a .docx document to S3/R2.
    Returns the S3 object key.
    """
    key = _build_document_key(user_id, submission_id)
    try:
        s3_client.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=file_bytes,
            ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            Metadata={
                "user_id": str(user_id),
                "submission_id": str(submission_id),
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        logger.info("Document uploaded", key=key, size=len(file_bytes))
        return key
    except ClientError as e:
        logger.error("Failed to upload document", error=str(e), key=key)
        raise


async def download_document(file_key: str) -> bytes:
    """Download a file from S3/R2 and return its bytes."""
    try:
        response = s3_client.get_object(Bucket=BUCKET, Key=file_key)
        return response["Body"].read()
    except ClientError as e:
        logger.error("Failed to download document", error=str(e), key=file_key)
        raise


async def generate_signed_url(file_key: str, expiry_seconds: int = 3600) -> str:
    """
    Generate a pre-signed URL for downloading a file.
    Never exposes bucket name or keys to the frontend.
    Default expiry: 1 hour.
    """
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET, "Key": file_key},
            ExpiresIn=expiry_seconds,
        )
        return url
    except ClientError as e:
        logger.error("Failed to generate signed URL", error=str(e), key=file_key)
        raise


async def delete_document(file_key: str) -> None:
    """Delete a file from S3/R2."""
    try:
        s3_client.delete_object(Bucket=BUCKET, Key=file_key)
        logger.info("Document deleted", key=file_key)
    except ClientError as e:
        logger.error("Failed to delete document", error=str(e), key=file_key)
        raise


async def upload_report_pdf(
    pdf_bytes: bytes,
    user_id: uuid.UUID,
    submission_id: uuid.UUID,
) -> str:
    """Upload a compliance report PDF to S3/R2. Returns the S3 key."""
    key = _build_report_key(user_id, submission_id)
    try:
        s3_client.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=pdf_bytes,
            ContentType="application/pdf",
        )
        logger.info("Report PDF uploaded", key=key)
        return key
    except ClientError as e:
        logger.error("Failed to upload report PDF", error=str(e), key=key)
        raise


async def upload_corrected_doc(
    doc_bytes: bytes,
    user_id: uuid.UUID,
    submission_id: uuid.UUID,
) -> str:
    """Upload a corrected .docx to S3/R2. Returns the S3 key."""
    key = _build_corrected_key(user_id, submission_id)
    try:
        s3_client.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=doc_bytes,
            ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        logger.info("Corrected document uploaded", key=key)
        return key
    except ClientError as e:
        logger.error("Failed to upload corrected doc", error=str(e), key=key)
        raise

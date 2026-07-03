"""
Report Pydantic Schemas — request/response models for compliance report endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional


class ViolationResponse(BaseModel):
    """Individual violation in a compliance report."""
    id: str
    page_number: Optional[int] = None
    section_name: Optional[str] = None
    element_type: str
    rule_name: str
    current_value: Optional[str] = None
    expected_value: Optional[str] = None
    severity: str
    is_auto_fixable: bool = True
    is_ai_detected: bool = False
    context_excerpt: Optional[str] = None
    affected_count: int = 1
    fix_applied: bool = False

    class Config:
        from_attributes = True


class DocumentMetadata(BaseModel):
    """Metadata about the parsed document."""
    page_count: int = 0
    word_count: int = 0
    detected_sections: list[str] = []


class ComplianceReportResponse(BaseModel):
    """Full compliance report response."""
    id: str
    submission_id: str
    compliance_score: float = 0.0
    total_violations: int = 0
    critical_count: int = 0
    warning_count: int = 0
    suggestion_count: int = 0
    estimated_fix_time_minutes: Optional[int] = None
    total_elements_checked: Optional[int] = None
    violations: list[ViolationResponse] = []
    document_metadata: Optional[DocumentMetadata] = None
    report_pdf_url: Optional[str] = None
    corrected_doc_url: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class ReportSummary(BaseModel):
    """Summary stats for a compliance report (no violations list)."""
    submission_id: str
    compliance_score: float
    total_violations: int
    critical_count: int
    warning_count: int
    suggestion_count: int
    estimated_fix_time_minutes: Optional[int] = None


class CorrectionRequest(BaseModel):
    """Request to apply selected corrections."""
    violation_ids: list[str] = Field(
        default=[],
        description="List of violation IDs to fix. Empty = fix all auto-fixable."
    )

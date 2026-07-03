"""
Report PDF Generator — generates professional compliance report PDFs using ReportLab.
Layout per Appendix B: Cover → Overview → Violation List → Footer.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import io
import structlog

logger = structlog.get_logger()

# Colors
GREEN = colors.HexColor("#10B981")
AMBER = colors.HexColor("#F59E0B")
RED = colors.HexColor("#EF4444")
DARK_BG = colors.HexColor("#0F172A")
INDIGO = colors.HexColor("#6366F1")
SLATE_200 = colors.HexColor("#E2E8F0")
SLATE_700 = colors.HexColor("#334155")
WHITE = colors.white


def _score_color(score: float) -> colors.Color:
    if score >= 80:
        return GREEN
    elif score >= 60:
        return AMBER
    return RED


def _severity_color(severity: str) -> colors.Color:
    if severity == "critical":
        return RED
    elif severity == "warning":
        return AMBER
    return colors.HexColor("#3B82F6")


def generate_report_pdf(
    filename: str,
    compliance_score: float,
    violations: list,
    ruleset_name: str,
    ruleset_version: str,
    doc_metadata: dict,
) -> bytes:
    """Generate a professional compliance report PDF. Returns PDF bytes."""
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            topMargin=2*cm, bottomMargin=2*cm,
            leftMargin=2.5*cm, rightMargin=2.5*cm,
        )

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="CoverTitle", fontSize=28, leading=34, alignment=TA_CENTER, textColor=INDIGO, spaceAfter=20, fontName="Helvetica-Bold"))
        styles.add(ParagraphStyle(name="CoverSubtitle", fontSize=14, leading=18, alignment=TA_CENTER, textColor=SLATE_700, spaceAfter=10))
        styles.add(ParagraphStyle(name="ScoreText", fontSize=48, leading=56, alignment=TA_CENTER, fontName="Helvetica-Bold", spaceAfter=20))
        styles.add(ParagraphStyle(name="SectionHeading", fontSize=16, leading=20, textColor=INDIGO, fontName="Helvetica-Bold", spaceAfter=12, spaceBefore=16))
        styles.add(ParagraphStyle(name="SmallText", fontSize=9, leading=12, textColor=SLATE_700))
        styles.add(ParagraphStyle(name="FooterText", fontSize=8, leading=10, alignment=TA_CENTER, textColor=SLATE_700))

        elements = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        # === PAGE 1: COVER ===
        elements.append(Spacer(1, 3*cm))
        elements.append(Paragraph("FormatGuard", styles["CoverTitle"]))
        elements.append(Paragraph("Formatting Compliance Report", styles["CoverSubtitle"]))
        elements.append(Spacer(1, 1.5*cm))

        score_color = _score_color(compliance_score)
        elements.append(Paragraph(
            f'<font color="{score_color.hexval()}">{compliance_score:.1f}%</font>',
            styles["ScoreText"]
        ))
        elements.append(Paragraph("Compliance Score", styles["CoverSubtitle"]))
        elements.append(Spacer(1, 1*cm))

        # Summary box
        critical_count = sum(1 for v in violations if getattr(v, 'severity', '') == "critical")
        warning_count = sum(1 for v in violations if getattr(v, 'severity', '') == "warning")
        suggestion_count = sum(1 for v in violations if getattr(v, 'severity', '') == "suggestion")

        summary_data = [
            ["Document", filename],
            ["Checked on", now],
            ["Ruleset", f"{ruleset_name} v{ruleset_version}"],
            ["Total Violations", str(len(violations))],
            ["Critical", str(critical_count)],
            ["Warnings", str(warning_count)],
            ["Suggestions", str(suggestion_count)],
        ]
        summary_table = Table(summary_data, colWidths=[5*cm, 10*cm])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), SLATE_200),
            ("TEXTCOLOR", (0, 0), (-1, -1), SLATE_700),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, SLATE_200),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(summary_table)
        elements.append(PageBreak())

        # === PAGE 2: DOCUMENT OVERVIEW ===
        elements.append(Paragraph("Document Overview", styles["SectionHeading"]))

        meta_data = [
            ["Pages", str(doc_metadata.get("page_count", "N/A"))],
            ["Word Count", str(doc_metadata.get("word_count", "N/A"))],
            ["Sections Detected", str(len(doc_metadata.get("detected_sections", [])))],
        ]
        meta_table = Table(meta_data, colWidths=[5*cm, 10*cm])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), SLATE_200),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, SLATE_200),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 1*cm))

        # Sections list
        sections = doc_metadata.get("detected_sections", [])
        if sections:
            elements.append(Paragraph("Detected Sections", styles["SectionHeading"]))
            for s in sections[:20]:
                elements.append(Paragraph(f"• {s}", styles["Normal"]))
            elements.append(Spacer(1, 0.5*cm))

        elements.append(PageBreak())

        # === PAGES 3+: VIOLATION LIST ===
        elements.append(Paragraph("Violation Details", styles["SectionHeading"]))

        if violations:
            header = ["#", "Page", "Element", "Rule", "Current", "Expected", "Severity"]
            table_data = [header]

            for i, v in enumerate(violations[:100]):  # Limit to 100 in PDF
                sev = getattr(v, 'severity', 'warning')
                table_data.append([
                    str(i + 1),
                    str(getattr(v, 'page_number', '-') or '-'),
                    str(getattr(v, 'element_type', '')),
                    str(getattr(v, 'rule_name', '')),
                    str(getattr(v, 'current_value', ''))[:30],
                    str(getattr(v, 'expected_value', ''))[:30],
                    sev.upper(),
                ])

            col_widths = [1*cm, 1.2*cm, 2.5*cm, 3*cm, 3*cm, 3*cm, 2*cm]
            viol_table = Table(table_data, colWidths=col_widths, repeatRows=1)

            # Style rows by severity
            style_cmds = [
                ("BACKGROUND", (0, 0), (-1, 0), INDIGO),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("PADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, SLATE_200),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, colors.HexColor("#F8FAFC")]),
            ]

            for i, v in enumerate(violations[:100]):
                row = i + 1
                sev = getattr(v, 'severity', 'warning')
                sev_col = _severity_color(sev)
                style_cmds.append(("TEXTCOLOR", (6, row), (6, row), sev_col))

            viol_table.setStyle(TableStyle(style_cmds))
            elements.append(viol_table)
        else:
            elements.append(Paragraph("No violations found. Your document is fully compliant!", styles["Normal"]))

        # === LAST PAGE: FOOTER ===
        elements.append(Spacer(1, 2*cm))
        elements.append(HRFlowable(width="100%", thickness=1, color=SLATE_200))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph("Generated by FormatGuard | formatguard.com", styles["FooterText"]))
        elements.append(Paragraph(
            "This report verifies formatting compliance only. It does not assess academic content quality.",
            styles["FooterText"]
        ))

        doc.build(elements)
        return buffer.getvalue()

    except Exception as e:
        logger.error("PDF generation failed", error=str(e))
        return None

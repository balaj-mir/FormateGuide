"""
Compliance Engine — evaluates a StructuredDocumentObject against a Ruleset
and produces an ordered list of Violation objects with compliance score.

Rule Types Supported:
  - EXACT_MATCH: string equality (case-insensitive)
  - NUMERIC_RANGE: value within ±tolerance
  - ENUM_MATCH: value must be in allowed set
  - BOOLEAN_CHECK: property must be true/false
  - PATTERN_MATCH: value matches regex
  - PRESENCE_CHECK: element must/must not exist
  - MARGIN_CHECK: page margin within ±1mm tolerance
  - SEMANTIC: AI-detected (handled separately in ai_service.py)
"""

from dataclasses import dataclass, field
from typing import Optional
import re
import uuid
import structlog

from app.services.document_parser import StructuredDocumentObject, ParagraphFormatting

logger = structlog.get_logger()

MARGIN_TOLERANCE_CM = 0.1  # ±1mm


@dataclass
class Violation:
    id: str = ""
    page_number: Optional[int] = None
    section_name: Optional[str] = None
    element_type: str = ""
    rule_name: str = ""
    current_value: str = ""
    expected_value: str = ""
    severity: str = "warning"
    is_auto_fixable: bool = True
    is_ai_detected: bool = False
    context_excerpt: Optional[str] = None
    affected_count: int = 1

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


def _check_exact_match(current: str, expected: str) -> bool:
    if current is None or expected is None:
        return current == expected
    return current.strip().lower() == expected.strip().lower()


def _check_numeric_range(current: float, expected: float, tolerance: float = 0.5) -> bool:
    if current is None or expected is None:
        return current == expected
    return abs(current - expected) <= tolerance


def _check_margin(current: float, expected: float) -> bool:
    if current is None:
        return False
    return abs(current - expected) <= MARGIN_TOLERANCE_CM


def _get_body_paragraphs(doc: StructuredDocumentObject) -> list[ParagraphFormatting]:
    return [p for p in doc.paragraphs
            if not p.is_heading and not p.is_caption and not p.is_reference
            and not p.is_list_item and p.text_preview.strip()]


def _get_heading_paragraphs(doc: StructuredDocumentObject, level: int) -> list[ParagraphFormatting]:
    return [p for p in doc.paragraphs if p.is_heading and p.heading_level == level]


def _batch_violation(
    paragraphs: list[ParagraphFormatting],
    check_fn,
    element_type: str,
    rule_name: str,
    expected_value: str,
    severity: str,
    is_auto_fixable: bool = True,
) -> Optional[Violation]:
    """Check a property across multiple paragraphs, batch into single violation."""
    failing = []
    for p in paragraphs:
        result = check_fn(p)
        if result is not None:
            failing.append((p, result))

    if not failing:
        return None

    first_p, first_val = failing[0]
    return Violation(
        page_number=first_p.page_number,
        section_name=first_p.style_name,
        element_type=element_type,
        rule_name=rule_name,
        current_value=str(first_val),
        expected_value=expected_value,
        severity=severity,
        is_auto_fixable=is_auto_fixable,
        context_excerpt=first_p.text_preview[:80] if first_p.text_preview else None,
        affected_count=len(failing),
    )


def _check_page_setup(doc: StructuredDocumentObject, rules: dict) -> tuple[list[Violation], int, int]:
    """Check page setup rules (margins, paper size, orientation)."""
    violations = []
    total = 0
    passed = 0
    ps_rules = rules.get("page_setup", {})
    if not ps_rules or not ps_rules.get("enabled", True):
        return violations, total, passed

    severity = ps_rules.get("severity", "critical")
    ps = doc.page_setup

    checks = [
        ("Paper Size", ps.paper_size, ps_rules.get("paper_size"), "page_setup"),
        ("Orientation", ps.orientation, ps_rules.get("orientation"), "page_setup"),
    ]
    for name, current, expected, etype in checks:
        if expected is None:
            continue
        total += 1
        if _check_exact_match(str(current), str(expected)):
            passed += 1
        else:
            violations.append(Violation(
                element_type=etype, rule_name=name,
                current_value=str(current), expected_value=str(expected),
                severity=severity, is_auto_fixable=False,
            ))

    margin_checks = [
        ("Top Margin", ps.margin_top_cm, ps_rules.get("margin_top_cm")),
        ("Bottom Margin", ps.margin_bottom_cm, ps_rules.get("margin_bottom_cm")),
        ("Left Margin", ps.margin_left_cm, ps_rules.get("margin_left_cm")),
        ("Right Margin", ps.margin_right_cm, ps_rules.get("margin_right_cm")),
    ]
    for name, current, expected in margin_checks:
        if expected is None:
            continue
        total += 1
        if _check_margin(current, expected):
            passed += 1
        else:
            violations.append(Violation(
                element_type="page_margin", rule_name=name,
                current_value=f"{current} cm", expected_value=f"{expected} cm",
                severity=severity, is_auto_fixable=True,
            ))

    return violations, total, passed


def _check_text_rules(
    paragraphs: list[ParagraphFormatting],
    rules: dict,
    element_type: str,
) -> tuple[list[Violation], int, int]:
    """Check text formatting rules for a group of paragraphs."""
    violations = []
    total = 0
    passed = 0

    if not rules or not rules.get("enabled", True) or not paragraphs:
        return violations, total, passed

    severity = rules.get("severity", "warning")
    tolerance = rules.get("font_size_tolerance_pt", 0.5)

    # Font family check
    expected_font = rules.get("font_family")
    if expected_font:
        total += 1
        v = _batch_violation(
            paragraphs,
            lambda p: p.font_family if p.font_family and not _check_exact_match(p.font_family, expected_font) else None,
            element_type, "Font Family", expected_font, severity,
        )
        if v:
            violations.append(v)
        else:
            passed += 1

    # Font size check
    expected_size = rules.get("font_size_pt")
    if expected_size is not None:
        total += 1
        v = _batch_violation(
            paragraphs,
            lambda p: p.font_size_pt if p.font_size_pt is not None and not _check_numeric_range(p.font_size_pt, expected_size, tolerance) else None,
            element_type, "Font Size", f"{expected_size} pt", severity,
        )
        if v:
            violations.append(v)
        else:
            passed += 1

    # Bold check
    expected_bold = rules.get("bold")
    if expected_bold is not None:
        total += 1
        v = _batch_violation(
            paragraphs,
            lambda p: p.bold if p.bold is not None and p.bold != expected_bold else None,
            element_type, "Bold", str(expected_bold), severity,
        )
        if v:
            violations.append(v)
        else:
            passed += 1

    # Italic check
    expected_italic = rules.get("italic")
    if expected_italic is not None:
        total += 1
        v = _batch_violation(
            paragraphs,
            lambda p: p.italic if p.italic is not None and p.italic != expected_italic else None,
            element_type, "Italic", str(expected_italic), severity,
        )
        if v:
            violations.append(v)
        else:
            passed += 1

    # Alignment check
    expected_align = rules.get("alignment")
    if expected_align:
        total += 1
        v = _batch_violation(
            paragraphs,
            lambda p: p.alignment if p.alignment and not _check_exact_match(p.alignment, expected_align) else None,
            element_type, "Alignment", expected_align, severity,
        )
        if v:
            violations.append(v)
        else:
            passed += 1

    # Line spacing check
    expected_spacing = rules.get("line_spacing")
    if expected_spacing is not None:
        total += 1
        v = _batch_violation(
            paragraphs,
            lambda p: p.line_spacing if p.line_spacing is not None and not _check_numeric_range(p.line_spacing, expected_spacing, 0.1) else None,
            element_type, "Line Spacing", str(expected_spacing), severity,
        )
        if v:
            violations.append(v)
        else:
            passed += 1

    return violations, total, passed


def _check_presence_rules(doc: StructuredDocumentObject, rules: dict) -> tuple[list[Violation], int, int]:
    """Check presence rules (TOC, references, cover page)."""
    violations = []
    total = 0
    passed = 0

    # Table of Contents
    toc_rules = rules.get("table_of_contents", {})
    if toc_rules.get("enabled", False) and toc_rules.get("required", False):
        total += 1
        if doc.has_table_of_contents:
            passed += 1
        else:
            violations.append(Violation(
                element_type="table_of_contents", rule_name="Table of Contents Required",
                current_value="Not found", expected_value="Present",
                severity=toc_rules.get("severity", "critical"), is_auto_fixable=False,
            ))

    # References section
    ref_rules = rules.get("references", {})
    if ref_rules.get("enabled", False) and ref_rules.get("required", False):
        total += 1
        if doc.has_references_section:
            passed += 1
        else:
            violations.append(Violation(
                element_type="reference", rule_name="References Section Required",
                current_value="Not found", expected_value="Present",
                severity=ref_rules.get("severity", "critical"), is_auto_fixable=False,
            ))

    return violations, total, passed


def _check_page_number_rules(doc: StructuredDocumentObject, rules: dict) -> tuple[list[Violation], int, int]:
    """Check page number position and format rules."""
    violations = []
    total = 0
    passed = 0
    pn_rules = rules.get("page_numbers", {})

    if not pn_rules or not pn_rules.get("enabled", True):
        return violations, total, passed

    severity = pn_rules.get("severity", "warning")
    hf = doc.header_footer

    expected_position = pn_rules.get("position")
    if expected_position:
        total += 1
        if hf.page_number_position and _check_exact_match(hf.page_number_position, expected_position):
            passed += 1
        else:
            violations.append(Violation(
                element_type="page_number", rule_name="Page Number Position",
                current_value=hf.page_number_position or "Not found",
                expected_value=expected_position,
                severity=severity, is_auto_fixable=True,
            ))

    return violations, total, passed


def run_compliance_check(
    document: StructuredDocumentObject,
    ruleset: dict,
) -> tuple[list[Violation], float]:
    """
    Returns (violations_list, compliance_score_percentage).
    Compliance score = (elements_passing / total_elements_checked) * 100
    """
    all_violations = []
    total_checks = 0
    passed_checks = 0

    rules = ruleset.get("rules", ruleset)

    # 1. Page setup rules
    v, t, p = _check_page_setup(document, rules)
    all_violations.extend(v)
    total_checks += t
    passed_checks += p

    # 2. Body text rules
    body_paras = _get_body_paragraphs(document)
    v, t, p = _check_text_rules(body_paras, rules.get("body_text", {}), "body_text")
    all_violations.extend(v)
    total_checks += t
    passed_checks += p

    # 3. Heading rules (H1-H6)
    for level in range(1, 7):
        key = f"heading_{level}"
        heading_rules = rules.get(key, {})
        if heading_rules:
            heading_paras = _get_heading_paragraphs(document, level)
            v, t, p = _check_text_rules(heading_paras, heading_rules, key)
            all_violations.extend(v)
            total_checks += t
            passed_checks += p

    # 4. Page number rules
    v, t, p = _check_page_number_rules(document, rules)
    all_violations.extend(v)
    total_checks += t
    passed_checks += p

    # 5. Presence rules (TOC, references)
    v, t, p = _check_presence_rules(document, rules)
    all_violations.extend(v)
    total_checks += t
    passed_checks += p

    # Assign display order
    for i, v in enumerate(all_violations):
        v.display_order = i + 1

    # Calculate compliance score
    compliance_score = (passed_checks / total_checks * 100) if total_checks > 0 else 100.0

    logger.info(
        "Compliance check complete",
        total_checks=total_checks,
        passed=passed_checks,
        violations=len(all_violations),
        score=round(compliance_score, 2),
    )

    return all_violations, round(compliance_score, 2)

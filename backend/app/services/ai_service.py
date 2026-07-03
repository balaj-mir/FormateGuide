"""
AI / NLP Service — uses OpenAI GPT-4o for semantic checks.
"""

import json
from openai import AsyncOpenAI
from app.config import settings
import structlog

logger = structlog.get_logger()

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def detect_citation_style(references_text: str, expected_style: str) -> list:
    """Detect citation style using GPT-4o and compare with expected."""
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a formatting expert. Analyze the provided reference list "
                        "and identify the citation style (IEEE, APA 7th, Harvard, Chicago, "
                        "Vancouver, MLA, or Unknown). Respond in JSON only: "
                        '{"detected_style": "...", "confidence": 0.0-1.0, "example_violations": ["..."]}'
                    ),
                },
                {"role": "user", "content": f"Expected style: {expected_style}\n\nReferences:\n{references_text[:3000]}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=500,
        )

        result = json.loads(response.choices[0].message.content)
        detected = result.get("detected_style", "Unknown")
        confidence = result.get("confidence", 0)

        if detected.lower() != expected_style.lower() and confidence > 0.7:
            from app.services.compliance_engine import Violation
            return [Violation(
                element_type="reference",
                rule_name="Citation Style",
                current_value=detected,
                expected_value=expected_style,
                severity="critical",
                is_auto_fixable=False,
                is_ai_detected=True,
                context_excerpt="; ".join(result.get("example_violations", [])[:3]),
            )]
        return []
    except Exception as e:
        logger.warning("AI citation detection failed", error=str(e))
        return []


async def classify_heading_levels(paragraphs: list, ruleset_heading_rules: dict) -> list:
    """Use GPT-4o for semantic heading classification when styles are ambiguous."""
    try:
        heading_texts = []
        for p in paragraphs:
            if hasattr(p, 'text_preview') and p.text_preview and len(p.text_preview) < 200:
                heading_texts.append(f"[idx={p.paragraph_index}] {p.text_preview}")
        if not heading_texts:
            return []

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Classify each line as a heading level (1-6) or 'body'. "
                        "Respond in JSON: {\"classifications\": [{\"index\": N, \"level\": N_or_null}]}"
                    ),
                },
                {"role": "user", "content": "\n".join(heading_texts[:50])},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=1000,
        )
        return json.loads(response.choices[0].message.content).get("classifications", [])
    except Exception as e:
        logger.warning("AI heading classification failed", error=str(e))
        return []


async def ai_import_ruleset_from_pdf(pdf_text: str, institution_name: str) -> dict:
    """Extract a structured Ruleset JSON from a formatting guideline PDF text."""
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract formatting rules from the provided guideline text and return "
                        "a JSON ruleset following the FormatGuard schema with keys: "
                        "page_setup, body_text, heading_1, heading_2, heading_3, "
                        "page_numbers, references, table_of_contents, cover_page. "
                        "Each rule should have: enabled, severity, and relevant properties."
                    ),
                },
                {"role": "user", "content": f"Institution: {institution_name}\n\nGuidelines:\n{pdf_text[:5000]}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=2000,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error("AI ruleset import failed", error=str(e))
        return {}

"""
Ruleset Service — CRUD operations, versioning, seeding pre-built rulesets.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.database import async_session_factory
from app.models.ruleset import Ruleset, RulesetVersion

logger = structlog.get_logger()

# Path to pre-built ruleset JSON files
RULESETS_DIR = Path(__file__).parent.parent.parent / "data" / "rulesets"


async def seed_prebuilt_rulesets() -> None:
    """
    Load all pre-built rulesets from JSON files into the database.
    Skips rulesets that already exist (by name match).
    Called on application startup.
    """
    if not RULESETS_DIR.exists():
        logger.warning("Rulesets directory not found", path=str(RULESETS_DIR))
        return

    async with async_session_factory() as session:
        for json_file in sorted(RULESETS_DIR.glob("*.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                name = data.get("name", json_file.stem)

                # Check if already exists
                result = await session.execute(
                    select(func.count(Ruleset.id)).where(Ruleset.name == name)
                )
                count = result.scalar()
                if count and count > 0:
                    logger.debug("Ruleset already exists, skipping", name=name)
                    continue

                ruleset = Ruleset(
                    name=name,
                    description=data.get("description", ""),
                    version=data.get("version", "1.0"),
                    is_public=data.get("is_public", True),
                    is_verified=True,  # Pre-built rulesets are verified
                    rules=data.get("rules", {}),
                )
                session.add(ruleset)
                await session.flush()

                # Also create initial version record
                version = RulesetVersion(
                    ruleset_id=ruleset.id,
                    version=ruleset.version,
                    rules=ruleset.rules,
                    change_log="Initial pre-built ruleset",
                )
                session.add(version)

                logger.info("Seeded ruleset", name=name, file=json_file.name)

            except Exception as e:
                logger.error(
                    "Failed to seed ruleset",
                    file=json_file.name,
                    error=str(e),
                )

        await session.commit()
    logger.info("Ruleset seeding complete")


async def create_ruleset(
    db: AsyncSession,
    name: str,
    description: str | None,
    rules: dict,
    created_by: uuid.UUID,
    institution_id: uuid.UUID | None = None,
    is_public: bool = False,
) -> Ruleset:
    """Create a new ruleset with initial version."""
    ruleset = Ruleset(
        name=name,
        description=description,
        rules=rules,
        created_by=created_by,
        institution_id=institution_id,
        is_public=is_public,
        version="1.0",
    )
    db.add(ruleset)
    await db.flush()

    # Create initial version record
    version = RulesetVersion(
        ruleset_id=ruleset.id,
        version="1.0",
        rules=rules,
        change_log="Initial version",
        created_by=created_by,
    )
    db.add(version)
    await db.flush()

    return ruleset


async def update_ruleset(
    db: AsyncSession,
    ruleset: Ruleset,
    rules: dict | None = None,
    name: str | None = None,
    description: str | None = None,
    is_public: bool | None = None,
    change_log: str | None = None,
    updated_by: uuid.UUID | None = None,
) -> Ruleset:
    """
    Update a ruleset. If rules change, increment version and save history.
    """
    if name is not None:
        ruleset.name = name
    if description is not None:
        ruleset.description = description
    if is_public is not None:
        ruleset.is_public = is_public

    if rules is not None and rules != ruleset.rules:
        # Increment version
        parts = ruleset.version.split(".")
        try:
            minor = int(parts[-1]) + 1
            new_version = f"{parts[0]}.{minor}"
        except (ValueError, IndexError):
            new_version = f"{ruleset.version}.1"

        ruleset.version = new_version
        ruleset.rules = rules

        # Save version history
        version = RulesetVersion(
            ruleset_id=ruleset.id,
            version=new_version,
            rules=rules,
            change_log=change_log or f"Updated to version {new_version}",
            created_by=updated_by,
        )
        db.add(version)

    await db.flush()
    return ruleset

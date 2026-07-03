"""
Rulesets Router — CRUD, marketplace, versioning, ratings, pre-built rulesets.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.ruleset import Ruleset, RulesetVersion
from app.models.rating import RulesetRating
from app.models.user import User
from app.schemas.ruleset import (
    RulesetCreate, RulesetUpdate, RulesetResponse, RulesetList, RulesetRatingCreate,
)
from app.services.ruleset_service import create_ruleset, update_ruleset

router = APIRouter()


def _ruleset_to_response(r: Ruleset) -> RulesetResponse:
    return RulesetResponse(
        id=str(r.id), name=r.name, description=r.description,
        institution_id=str(r.institution_id) if r.institution_id else None,
        created_by=str(r.created_by) if r.created_by else None,
        version=r.version, is_public=r.is_public, is_verified=r.is_verified,
        download_count=r.download_count,
        rating_avg=float(r.rating_avg) if r.rating_avg else None,
        rules=r.rules, created_at=r.created_at.isoformat(),
        updated_at=r.updated_at.isoformat(),
    )


@router.get("", response_model=RulesetList)
async def list_rulesets(
    page: int = 1, limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's rulesets + public rulesets."""
    offset = (page - 1) * limit
    query = select(Ruleset).where(
        or_(Ruleset.created_by == current_user.id, Ruleset.is_public == True)
    ).order_by(Ruleset.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    rulesets = result.scalars().all()

    count_result = await db.execute(
        select(func.count(Ruleset.id)).where(
            or_(Ruleset.created_by == current_user.id, Ruleset.is_public == True)
        )
    )
    total = count_result.scalar() or 0

    return RulesetList(
        rulesets=[_ruleset_to_response(r) for r in rulesets],
        total=total, page=page, limit=limit,
    )


@router.post("", response_model=RulesetResponse, status_code=201)
async def create_new_ruleset(
    data: RulesetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new ruleset."""
    ruleset = await create_ruleset(
        db, name=data.name, description=data.description,
        rules=data.rules, created_by=current_user.id,
        institution_id=current_user.institution_id, is_public=data.is_public,
    )
    return _ruleset_to_response(ruleset)


@router.get("/marketplace", response_model=RulesetList)
async def marketplace(
    search: str = None, page: int = 1, limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Public ruleset marketplace."""
    query = select(Ruleset).where(Ruleset.is_public == True)
    if search:
        query = query.where(Ruleset.name.ilike(f"%{search}%"))
    query = query.order_by(Ruleset.download_count.desc()).offset((page-1)*limit).limit(limit)

    result = await db.execute(query)
    rulesets = result.scalars().all()

    count_query = select(func.count(Ruleset.id)).where(Ruleset.is_public == True)
    if search:
        count_query = count_query.where(Ruleset.name.ilike(f"%{search}%"))
    total = (await db.execute(count_query)).scalar() or 0

    return RulesetList(rulesets=[_ruleset_to_response(r) for r in rulesets], total=total, page=page, limit=limit)


@router.get("/prebuilt", response_model=RulesetList)
async def list_prebuilt(db: AsyncSession = Depends(get_db)):
    """List all pre-built verified rulesets."""
    result = await db.execute(
        select(Ruleset).where(Ruleset.is_verified == True).order_by(Ruleset.name)
    )
    rulesets = result.scalars().all()
    return RulesetList(rulesets=[_ruleset_to_response(r) for r in rulesets], total=len(rulesets), page=1, limit=100)


@router.get("/{ruleset_id}", response_model=RulesetResponse)
async def get_ruleset(ruleset_id: str, db: AsyncSession = Depends(get_db)):
    """Get ruleset detail."""
    result = await db.execute(select(Ruleset).where(Ruleset.id == uuid.UUID(ruleset_id)))
    ruleset = result.scalar_one_or_none()
    if not ruleset:
        raise HTTPException(status_code=404, detail="Ruleset not found")
    return _ruleset_to_response(ruleset)


@router.put("/{ruleset_id}", response_model=RulesetResponse)
async def update_existing_ruleset(
    ruleset_id: str, data: RulesetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update ruleset (creates new version if rules change)."""
    result = await db.execute(select(Ruleset).where(Ruleset.id == uuid.UUID(ruleset_id)))
    ruleset = result.scalar_one_or_none()
    if not ruleset:
        raise HTTPException(status_code=404, detail="Ruleset not found")
    if ruleset.created_by != current_user.id and current_user.role not in ("institutional_admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Not authorized to edit this ruleset")

    ruleset = await update_ruleset(
        db, ruleset, rules=data.rules, name=data.name,
        description=data.description, is_public=data.is_public,
        change_log=data.change_log, updated_by=current_user.id,
    )
    return _ruleset_to_response(ruleset)


@router.delete("/{ruleset_id}", status_code=204)
async def delete_ruleset(
    ruleset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a ruleset."""
    result = await db.execute(select(Ruleset).where(Ruleset.id == uuid.UUID(ruleset_id)))
    ruleset = result.scalar_one_or_none()
    if not ruleset:
        raise HTTPException(status_code=404, detail="Ruleset not found")
    if ruleset.created_by != current_user.id and current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    await db.delete(ruleset)


@router.post("/{ruleset_id}/import", response_model=RulesetResponse)
async def import_ruleset(
    ruleset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Import a public ruleset to user's library (creates a copy)."""
    result = await db.execute(select(Ruleset).where(Ruleset.id == uuid.UUID(ruleset_id)))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Ruleset not found")

    copy = await create_ruleset(
        db, name=f"{source.name} (Copy)", description=source.description,
        rules=source.rules, created_by=current_user.id, is_public=False,
    )
    source.download_count += 1
    await db.flush()
    return _ruleset_to_response(copy)


@router.post("/{ruleset_id}/rate")
async def rate_ruleset(
    ruleset_id: str, data: RulesetRatingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rate a marketplace ruleset."""
    rid = uuid.UUID(ruleset_id)
    # Check existing rating
    existing = await db.execute(
        select(RulesetRating).where(
            RulesetRating.ruleset_id == rid, RulesetRating.user_id == current_user.id
        )
    )
    rating = existing.scalar_one_or_none()

    if rating:
        rating.rating = data.rating
        rating.review = data.review
    else:
        rating = RulesetRating(
            ruleset_id=rid, user_id=current_user.id,
            rating=data.rating, review=data.review,
        )
        db.add(rating)

    await db.flush()

    # Update average rating
    avg_result = await db.execute(
        select(func.avg(RulesetRating.rating)).where(RulesetRating.ruleset_id == rid)
    )
    avg = avg_result.scalar()
    ruleset_result = await db.execute(select(Ruleset).where(Ruleset.id == rid))
    ruleset = ruleset_result.scalar_one_or_none()
    if ruleset and avg:
        ruleset.rating_avg = round(float(avg), 2)

    return {"message": "Rating submitted", "rating": data.rating}

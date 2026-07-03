"""
Admin Router — Institutional admin and super admin endpoints.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.models.submission import Submission
from app.models.report import ComplianceReport
from app.models.violation import Violation
from app.models.ruleset import Ruleset
from app.schemas.user import UserProfile, UserRoleUpdate

router = APIRouter()


@router.get("/submissions")
async def admin_list_submissions(
    page: int = 1, limit: int = 20, status: str = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """All submissions for admin's institution."""
    query = select(Submission).join(User, Submission.user_id == User.id)
    if admin.role == "institutional_admin" and admin.institution_id:
        query = query.where(User.institution_id == admin.institution_id)
    if status:
        query = query.where(Submission.status == status)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(Submission.created_at.desc()).offset((page-1)*limit).limit(limit)
    result = await db.execute(query)
    submissions = result.scalars().all()

    return {
        "submissions": [
            {"id": str(s.id), "user_id": str(s.user_id), "filename": s.original_filename,
             "status": s.status, "created_at": s.created_at.isoformat()}
            for s in submissions
        ],
        "total": total, "page": page, "limit": limit,
    }


@router.get("/analytics")
async def admin_analytics(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Aggregated violation analytics."""
    # Total submissions
    sub_q = select(func.count(Submission.id))
    if admin.institution_id and admin.role == "institutional_admin":
        sub_q = sub_q.join(User).where(User.institution_id == admin.institution_id)
    total_submissions = (await db.execute(sub_q)).scalar() or 0

    # Active users
    user_q = select(func.count(User.id)).where(User.is_active == True)
    if admin.institution_id and admin.role == "institutional_admin":
        user_q = user_q.where(User.institution_id == admin.institution_id)
    active_users = (await db.execute(user_q)).scalar() or 0

    # Average compliance score
    avg_q = select(func.avg(ComplianceReport.compliance_score))
    avg_score = (await db.execute(avg_q)).scalar()

    # Published rulesets count
    rs_q = select(func.count(Ruleset.id)).where(Ruleset.is_public == True)
    if admin.institution_id and admin.role == "institutional_admin":
        rs_q = rs_q.where(Ruleset.institution_id == admin.institution_id)
    rulesets_count = (await db.execute(rs_q)).scalar() or 0

    return {
        "total_submissions": total_submissions,
        "active_users": active_users,
        "avg_compliance_score": round(float(avg_score), 2) if avg_score else 0,
        "published_rulesets": rulesets_count,
    }


@router.get("/analytics/heatmap")
async def admin_heatmap(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Violation frequency heatmap data."""
    result = await db.execute(
        select(Violation.rule_name, func.count(Violation.id).label("count"))
        .group_by(Violation.rule_name)
        .order_by(func.count(Violation.id).desc())
        .limit(20)
    )
    data = [{"rule": row[0], "count": row[1]} for row in result.all()]
    return {"heatmap": data}


@router.get("/users")
async def admin_list_users(
    page: int = 1, limit: int = 20,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List users for admin's institution."""
    query = select(User)
    if admin.institution_id and admin.role == "institutional_admin":
        query = query.where(User.institution_id == admin.institution_id)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(User.created_at.desc()).offset((page-1)*limit).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "users": [
            UserProfile(
                id=str(u.id), email=u.email, full_name=u.full_name,
                role=u.role, subscription_tier=u.subscription_tier,
                institution_id=str(u.institution_id) if u.institution_id else None,
                monthly_checks_used=u.monthly_checks_used,
                is_active=u.is_active, created_at=u.created_at.isoformat(),
            ).model_dump()
            for u in users
        ],
        "total": total, "page": page, "limit": limit,
    }


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str, data: UserRoleUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a user's role."""
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if admin.role == "institutional_admin" and user.institution_id != admin.institution_id:
        raise HTTPException(status_code=403, detail="Cannot modify users outside your institution")

    user.role = data.role
    await db.flush()
    return {"message": f"User role updated to {data.role}"}


@router.get("/rulesets")
async def admin_list_rulesets(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Institution-level ruleset management."""
    query = select(Ruleset)
    if admin.institution_id and admin.role == "institutional_admin":
        query = query.where(Ruleset.institution_id == admin.institution_id)
    result = await db.execute(query.order_by(Ruleset.created_at.desc()))
    rulesets = result.scalars().all()

    return {
        "rulesets": [
            {"id": str(r.id), "name": r.name, "version": r.version,
             "is_public": r.is_public, "is_verified": r.is_verified,
             "download_count": r.download_count}
            for r in rulesets
        ]
    }

"""Admin endpoints: user management, audit log."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.audit_log import AuditLog
from app.models.role import Role
from app.models.user import User
from app.schemas.audit import AuditLogEntry, AuditLogListResponse
from app.schemas.auth import UserListItem, UserListResponse, UserUpdateRequest
from app.services.auth_service import AuthService, write_audit_log

router = APIRouter()


@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("users", "full")),
) -> UserListResponse:
    """API-095: List all users (admin, paginated)."""
    query = select(User).where(User.deleted_at.is_(None))

    if search:
        query = query.where(
            (func.lower(User.email).contains(search.lower()))
            | (func.lower(User.full_name).contains(search.lower()))
        )

    # Count total
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Paginate
    query = query.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()

    return UserListResponse(
        items=[
            UserListItem(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                phone=u.phone,
                role=u.role.name,
                is_active=u.is_active,
                last_login_at=u.last_login_at,
            )
            for u in users
        ],
        total=total,
        page=page,
        limit=limit,
    )


@router.patch("/users/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("users", "full")),
):
    """API-096: Update user role/status."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")

    service = AuthService(db)
    changes = []

    if data.role is not None and data.role != user.role.name:
        role_result = await db.execute(select(Role).where(Role.name == data.role))
        new_role = role_result.scalar_one_or_none()
        if not new_role:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail=f"Role '{data.role}' not found")
        old_role = user.role.name
        user.role_id = new_role.id
        changes.append(f"role: {old_role} → {data.role}")
        # Force re-login: revoke all refresh tokens
        await service.revoke_all_user_tokens(user.id)
        await write_audit_log(
            db, action="user.role_changed", user_id=current_user.id,
            entity_type="user", entity_id=user.id,
            description=f"Changed role from {old_role} to {data.role}",
        )

    if data.is_active is not None and data.is_active != user.is_active:
        user.is_active = data.is_active
        if not data.is_active:
            await service.revoke_all_user_tokens(user.id)
        action = "user.enabled" if data.is_active else "user.disabled"
        await write_audit_log(
            db, action=action, user_id=current_user.id,
            entity_type="user", entity_id=user.id,
        )

    if data.full_name is not None:
        user.full_name = data.full_name
    if data.phone is not None:
        user.phone = data.phone

    await db.flush()

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": user.role.name,
        "permissions": user.role.permissions,
        "is_active": user.is_active,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
    }


@router.get("/audit-log")
async def list_audit_log(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    action_filter: str | None = None,
    user_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("audit", "full")),
) -> AuditLogListResponse:
    """API-097: View audit log (admin only)."""
    query = select(AuditLog)

    if action_filter:
        query = query.where(AuditLog.action.contains(action_filter))
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if date_from:
        query = query.where(AuditLog.created_at >= date_from)
    if date_to:
        query = query.where(AuditLog.created_at <= date_to)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    entries = result.scalars().all()

    return AuditLogListResponse(
        items=[
            AuditLogEntry(
                id=e.id,
                user_id=e.user_id,
                action=e.action,
                entity_type=e.entity_type,
                entity_id=e.entity_id,
                description=e.description,
                metadata_=e.metadata_,
                ip_address=e.ip_address,
                created_at=e.created_at,
            )
            for e in entries
        ],
        total=total,
        page=page,
        limit=limit,
    )

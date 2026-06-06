"""Admin endpoints: user management, audit log."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.role import Role
from app.models.user import User
from app.schemas.audit import AuditLogEntry, AuditLogListResponse
from app.schemas.auth import (
    AdminResetPasswordRequest,
    RegisterRequest,
    UserListItem,
    UserListResponse,
    UserUpdateRequest,
)
from app.schemas.settings import (
    DatabaseIntegrityResponse,
    DatabaseRepairResponse,
    DatabaseResetResponse,
    DatabaseRestoreResponse,
    ServiceHealthResponse,
    SettingsResponse,
    SettingsUpdateRequest,
    SettingsUpdateResponse,
)
from app.services.auth_service import AuthService, write_audit_log
from app.services.db_maintenance_service import DbMaintenanceService
from app.services.scraper_service import ScraperService
from app.services.settings_service import GROUP_LABELS, SettingsService

router = APIRouter()


def _get_ip(request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


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


@router.post("/users", status_code=201)
async def create_user(
    data: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("users", "full")),
):
    """API: Create a new user (admin only)."""
    service = AuthService(db)
    user = await service.register(data, current_user.id, ip_address=_get_ip(request))
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": user.role.name,
        "permissions": user.role.permissions,
        "is_active": user.is_active,
        "last_login_at": None,
    }


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


@router.post("/users/{user_id}/reset-password")
async def admin_reset_password(
    user_id: uuid.UUID,
    data: AdminResetPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("users", "full")),
):
    """API: Admin reset a user's password."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(data.new_password)

    service = AuthService(db)
    await service.revoke_all_user_tokens(user.id)
    await write_audit_log(
        db,
        action="user.password_reset",
        user_id=current_user.id,
        entity_type="user",
        entity_id=user.id,
        description=f"Admin reset password for {user.email}",
        ip_address=_get_ip(request),
    )
    await db.flush()

    return {"message": "Password reset successfully"}


# ── System Settings ──────────────────────────────────────


@router.get("/settings")
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("settings", "full")),
) -> SettingsResponse:
    """API: Get all system settings grouped."""
    service = SettingsService(db)
    items = await service.get_all_settings()
    return SettingsResponse(settings=items, groups=GROUP_LABELS)


@router.put("/settings")
async def update_settings(
    data: SettingsUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("settings", "full")),
) -> SettingsUpdateResponse:
    """API: Update editable system settings."""
    service = SettingsService(db)
    updated = await service.update_settings(data.updates, current_user.id)
    return SettingsUpdateResponse(updated=updated)


@router.get("/settings/health")
async def settings_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("settings", "full")),
) -> ServiceHealthResponse:
    """API: Check connectivity to PostgreSQL, Redis, and Ollama."""
    service = SettingsService(db)
    health = await service.check_service_health()
    return ServiceHealthResponse(**health)


# ── Data Scraping & Import ───────────────────────────────


@router.post("/scrape/city")
async def scrape_city(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("settings", "full")),
):
    """API: Scrape hospitals or NGOs for a given city. Returns preview only (no DB writes)."""
    city = (data.get("city") or "").strip()
    entity_type = (data.get("entity_type") or "").strip().lower()
    state = (data.get("state") or "").strip() or None

    if not city:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="City name is required")
    if entity_type not in ("hospitals", "ngos", "doctors"):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="entity_type must be 'hospitals', 'ngos', or 'doctors'")

    service = ScraperService(db)
    records = await service.scrape_city(city, entity_type, state=state)
    return {
        "records": records,
        "count": len(records),
        "city": city.title(),
    }


@router.post("/scrape/hospitals")
async def scrape_hospitals(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("settings", "full")),
):
    """API: Scrape hospital listings from a TN district page. Returns preview only."""
    url = data.get("url", "").strip()
    if not url:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="URL is required")
    if ".nic.in" not in url:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Only .nic.in district URLs are supported")

    service = ScraperService(db)
    records = await service.scrape_tn_district(url)
    return {"records": records, "count": len(records)}


@router.post("/import/hospitals")
async def import_hospitals(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("settings", "full")),
):
    """API: Bulk import hospitals from a JSON array."""
    hospitals = data.get("hospitals", [])
    if not hospitals:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="No hospitals provided")

    service = ScraperService(db)
    result = await service.bulk_import_hospitals(hospitals, current_user.id)
    return result


@router.post("/import/hospitals/csv")
async def import_hospitals_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("settings", "full")),
):
    """API: Import hospitals from a CSV file."""
    content = await file.read()
    service = ScraperService(db)
    records, parse_errors = service.parse_hospitals_csv(content)
    if not records:
        return {"imported": 0, "skipped": 0, "errors": parse_errors or ["No valid records found"]}

    result = await service.bulk_import_hospitals(records, current_user.id)
    result["errors"].extend(parse_errors)
    return result


@router.post("/import/ngos")
async def import_ngos(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("settings", "full")),
):
    """API: Bulk import NGOs/funding programs from a JSON array."""
    ngos = data.get("ngos", [])
    if not ngos:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="No NGOs provided")

    service = ScraperService(db)
    result = await service.bulk_import_ngos(ngos, current_user.id)
    return result


@router.post("/import/doctors")
async def import_doctors(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("settings", "full")),
):
    """API: Bulk import doctors from a JSON array."""
    doctors = data.get("doctors", [])
    if not doctors:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="No doctors provided")

    service = ScraperService(db)
    result = await service.bulk_import_doctors(doctors, current_user.id)
    return result


@router.post("/import/ngos/csv")
async def import_ngos_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("settings", "full")),
):
    """API: Import NGOs/funding programs from a CSV file."""
    content = await file.read()
    service = ScraperService(db)
    records, parse_errors = service.parse_ngos_csv(content)
    if not records:
        return {"imported": 0, "skipped": 0, "errors": parse_errors or ["No valid records found"]}

    result = await service.bulk_import_ngos(records, current_user.id)
    result["errors"].extend(parse_errors)
    return result


# ── Deduplication ────────────────────────────────────────


@router.post("/dedup/hospitals")
async def dedup_hospitals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("settings", "full")),
):
    """API: Find and remove duplicate hospitals (by name + city). Keeps the record with the most data."""
    from app.models.hospital import Hospital

    result = await db.execute(
        select(Hospital).where(Hospital.is_active.is_(True)).order_by(Hospital.created_at)
    )
    hospitals = result.scalars().all()

    # Group by lowercase(name + city)
    from collections import defaultdict
    groups: dict[str, list] = defaultdict(list)
    for h in hospitals:
        key = f"{h.name.strip().lower()}||{h.city.strip().lower()}"
        groups[key].append(h)

    removed = 0
    for _key, group in groups.items():
        if len(group) < 2:
            continue
        # Score each record by number of non-null/non-empty fields
        def _score(h: Hospital) -> int:
            return sum(1 for f in [h.address, h.phone, h.email, h.website, h.specialties, h.state]
                       if f)
        group.sort(key=_score, reverse=True)
        # Keep the first (richest), archive the rest
        for dup in group[1:]:
            dup.is_active = False
            removed += 1

    await db.flush()

    if removed > 0:
        from app.services.auth_service import write_audit_log
        await write_audit_log(
            db, action="dedup.hospitals", user_id=current_user.id,
            description=f"Removed {removed} duplicate hospitals",
        )

    return {"removed": removed, "kept": len(groups)}


@router.post("/dedup/funding")
async def dedup_funding(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("settings", "full")),
):
    """API: Find and remove duplicate funding programs (by name). Keeps the record with the most data."""
    from app.models.funding_program import FundingProgram

    result = await db.execute(
        select(FundingProgram).where(FundingProgram.is_active.is_(True)).order_by(FundingProgram.created_at)
    )
    programs = result.scalars().all()

    from collections import defaultdict
    groups: dict[str, list] = defaultdict(list)
    for p in programs:
        key = p.name.strip().lower()
        groups[key].append(p)

    removed = 0
    for _key, group in groups.items():
        if len(group) < 2:
            continue
        def _score(p: FundingProgram) -> int:
            return sum(1 for f in [p.description, p.provider, p.program_type,
                                    p.eligibility_criteria, p.application_url,
                                    p.contact_email, p.contact_phone] if f)
        group.sort(key=_score, reverse=True)
        for dup in group[1:]:
            dup.is_active = False
            removed += 1

    await db.flush()

    if removed > 0:
        from app.services.auth_service import write_audit_log
        await write_audit_log(
            db, action="dedup.funding", user_id=current_user.id,
            description=f"Removed {removed} duplicate funding programs",
        )

    return {"removed": removed, "kept": len(groups)}


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


# ── Database Maintenance ─────────────────────────────────


@router.get("/database/integrity")
async def database_integrity(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("settings", "full")),
) -> DatabaseIntegrityResponse:
    """API: Check database table integrity and health."""
    service = DbMaintenanceService(db)
    result = await service.integrity_check()
    return DatabaseIntegrityResponse(**result)


@router.post("/database/backup")
async def database_backup(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("settings", "full")),
):
    """API: Download a full database backup (pg_dump)."""
    service = DbMaintenanceService(db)

    await write_audit_log(
        db, action="database.backup", user_id=current_user.id,
        entity_type="database", description="Database backup downloaded",
    )
    await db.flush()

    dump_bytes = await service.backup_database()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"patient_nav_backup_{timestamp}.sql"

    return Response(
        content=dump_bytes,
        media_type="application/sql",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/database/restore")
async def database_restore(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("settings", "full")),
) -> DatabaseRestoreResponse:
    """API: Restore database from a SQL dump file."""
    content = await file.read()
    if not content:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="No file provided")

    service = DbMaintenanceService(db)
    result = await service.restore_database(current_user.id, content)
    return DatabaseRestoreResponse(**result)


@router.post("/database/repair")
async def database_repair(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("settings", "full")),
) -> DatabaseRepairResponse:
    """API: Run REINDEX and VACUUM on all tables."""
    service = DbMaintenanceService(db)
    result = await service.repair_database(current_user.id)
    return DatabaseRepairResponse(**result)


@router.post("/database/reset")
async def database_reset(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("settings", "full")),
) -> DatabaseResetResponse:
    """API: Reset database — drop and recreate all tables. Requires confirm='RESET'."""
    if data.get("confirm") != "RESET":
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Confirmation required. Send {\"confirm\": \"RESET\"}")

    service = DbMaintenanceService(db)
    result = await service.reset_database(current_user.id)
    return DatabaseResetResponse(**result)

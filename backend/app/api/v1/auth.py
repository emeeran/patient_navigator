"""Authentication endpoints: register, login, refresh, logout, me."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    UserProfileUpdateRequest,
)
from app.core.security import hash_password, verify_password
from app.services.auth_service import AuthService, write_audit_log
from app.services.rate_limiter import check_rate_limit, clear_rate_limit, record_failed_attempt

router = APIRouter()


def _get_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/register", status_code=201)
async def register(
    data: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """API-001: Register a new user (admin only)."""
    # Check admin permission
    from app.api.deps import require_role
    checker = require_role("admin")
    await checker(current_user)

    service = AuthService(db)
    user = await service.register(data, current_user.id, ip_address=_get_ip(request))
    return _serialize_user_profile(user)


@router.post("/login")
async def login(
    data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """API-002: Authenticate and receive tokens."""
    ip = _get_ip(request)
    await check_rate_limit(data.email, ip)

    service = AuthService(db)
    try:
        result = await service.login(data, ip_address=ip)
        await clear_rate_limit(data.email, ip)
        return result
    except Exception as e:
        from app.core.exceptions import AccountDisabledError, InvalidCredentialsError
        if isinstance(e, (InvalidCredentialsError, AccountDisabledError)):
            await record_failed_attempt(data.email, ip)
        raise


@router.post("/refresh")
async def refresh(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """API-003: Rotate access + refresh tokens."""
    service = AuthService(db)
    return await service.refresh_token(data.refresh_token)


@router.post("/logout")
async def logout(
    data: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """API-004: Invalidate refresh token."""
    service = AuthService(db)
    await service.logout(data.refresh_token, current_user.id)
    return {"message": "Logged out successfully"}


@router.get("/me")
async def me(
    current_user: User = Depends(get_current_active_user),
):
    """API-005: Get current user profile."""
    return _serialize_user_profile(current_user)


def _serialize_user_profile(user: User) -> dict:
    """Serialize user to profile dict."""
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


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """API: Change the current user's password."""
    if not verify_password(data.current_password, current_user.password_hash):
        from app.core.exceptions import InvalidCredentialsError
        raise InvalidCredentialsError("Current password is incorrect")

    current_user.password_hash = hash_password(data.new_password)

    service = AuthService(db)
    await service.revoke_all_user_tokens(current_user.id)
    await write_audit_log(
        db,
        action="user.password_changed",
        user_id=current_user.id,
        description="User changed their password",
        ip_address=_get_ip(request),
    )
    await db.flush()

    return {"message": "Password changed successfully. Please log in again."}


@router.patch("/me")
async def update_profile(
    data: UserProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """API: Update the current user's profile (name, phone)."""
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.phone is not None:
        current_user.phone = data.phone

    await db.flush()
    return _serialize_user_profile(current_user)

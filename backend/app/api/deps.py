"""FastAPI dependencies: current user extraction and RBAC enforcement."""

from collections.abc import Callable

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import InsufficientPermissionsError
from app.models.user import User
from app.services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Permission hierarchy: higher number = more access
LEVEL_RANK = {"full": 4, "read": 3, "review": 3, "own": 2, "none": 0}


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the current user from the Bearer token."""
    service = AuthService(db)
    return await service.get_current_user(token)


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Return the current user only if their account is active."""
    if not current_user.is_active:
        from app.core.exceptions import AccountDisabledError
        raise AccountDisabledError()
    return current_user


def has_permission(user_permissions: dict, resource: str, required_level: str) -> bool:
    """Check if user's permission level for a resource meets the requirement."""
    user_level = user_permissions.get(resource, "none")
    return LEVEL_RANK.get(user_level, 0) >= LEVEL_RANK.get(required_level, 0)


def require_permission(resource: str, level: str) -> Callable:
    """FastAPI dependency that checks if current user has the required permission."""

    async def _check(current_user: User = Depends(get_current_active_user)) -> User:
        perms = current_user.role.permissions if current_user.role else {}
        if not has_permission(perms, resource, level):
            raise InsufficientPermissionsError()
        return current_user

    return _check


def require_role(*roles: str) -> Callable:
    """FastAPI dependency that checks if current user has one of the required roles."""

    async def _check(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role.name not in roles:
            raise InsufficientPermissionsError()
        return current_user

    return _check

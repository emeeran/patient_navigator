"""Authentication business logic — register, login, refresh, logout."""

import uuid
from datetime import UTC, datetime

from jose import JWTError
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AccountDisabledError,
    DuplicateEmailError,
    InvalidCredentialsError,
    InvalidTokenError,
    TokenExpiredError,
    TokenReuseDetectedError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token_jti,
    verify_password,
)
from app.models.audit_log import AuditLog
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest


async def write_audit_log(
    db: AsyncSession,
    action: str,
    user_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    description: str | None = None,
    metadata: dict | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Write an entry to the audit log."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        metadata_=metadata,
        ip_address=ip_address,
    )
    db.add(entry)
    await db.flush()
    return entry


class AuthService:
    """Handles all authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(
        self,
        data: RegisterRequest,
        actor_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> User:
        """Register a new user. Returns the created User (password_hash never exposed)."""
        # Check email uniqueness (case-insensitive)
        existing = await self.db.execute(
            select(User).where(func.lower(User.email) == data.email.lower())
        )
        if existing.scalar_one_or_none():
            raise DuplicateEmailError()

        # Look up role
        role_result = await self.db.execute(select(Role).where(Role.name == data.role))
        role = role_result.scalar_one_or_none()
        if not role:
            raise InvalidCredentialsError(f"Role '{data.role}' not found")

        user = User(
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            phone=data.phone,
            role_id=role.id,
            is_active=True,
        )
        self.db.add(user)
        await self.db.flush()
        # Refresh to load the role relationship
        await self.db.refresh(user, ["role"])

        await write_audit_log(
            self.db,
            action="user.registered",
            user_id=actor_id,
            entity_type="user",
            entity_id=user.id,
            description=f"Registered user {user.email} with role {data.role}",
            ip_address=ip_address,
        )
        return user

    async def login(
        self,
        data: LoginRequest,
        ip_address: str | None = None,
    ) -> dict:
        """Authenticate user and return tokens + profile."""
        # Look up user (case-insensitive email)
        result = await self.db.execute(
            select(User).where(func.lower(User.email) == data.email.lower())
        )
        user = result.scalar_one_or_none()

        # Same error for both "not found" and "wrong password" (no enumeration)
        if not user or not verify_password(data.password, user.password_hash):
            await write_audit_log(
                self.db,
                action="user.login_failed",
                description=f"Failed login for {data.email}",
                ip_address=ip_address,
            )
            raise InvalidCredentialsError()

        if not user.is_active:
            await write_audit_log(
                self.db,
                action="user.login_disabled",
                user_id=user.id,
                description=f"Login attempt on disabled account {user.email}",
                ip_address=ip_address,
            )
            raise AccountDisabledError()

        # Create tokens
        access_token = create_access_token(user.id, user.role.name, user.role.permissions)
        refresh_jwt, jti = create_refresh_token(user.id)

        # Store refresh token hash
        rt = RefreshToken(
            token_hash=hash_token_jti(jti),
            user_id=user.id,
            expires_at=datetime.now(UTC) + __import__("datetime").timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.db.add(rt)

        # Update last_login_at
        user.last_login_at = datetime.now(UTC)
        await self.db.flush()

        await write_audit_log(
            self.db,
            action="user.login",
            user_id=user.id,
            description=f"User {user.email} logged in",
            ip_address=ip_address,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_jwt,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": _user_profile(user),
        }

    async def refresh_token(self, refresh_jwt: str) -> dict:
        """Rotate a refresh token. Old token is invalidated."""
        try:
            payload = decode_token(refresh_jwt)
        except JWTError:
            raise InvalidTokenError() from None

        if payload.get("type") != "refresh":
            raise InvalidTokenError()

        jti = payload.get("jti")
        user_id = payload.get("sub")
        if not jti or not user_id:
            raise InvalidTokenError()

        # Look up stored token hash
        token_hash = hash_token_jti(jti)
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        stored_token = result.scalar_one_or_none()

        if not stored_token:
            # Token reuse detected — revoke ALL user tokens
            await self._revoke_all_user_tokens(uuid.UUID(user_id))
            await write_audit_log(
                self.db,
                action="security.token_reuse_detected",
                user_id=uuid.UUID(user_id),
                description="Refresh token reuse detected, all tokens revoked",
            )
            raise TokenReuseDetectedError()

        if stored_token.revoked:
            await self._revoke_all_user_tokens(uuid.UUID(user_id))
            await write_audit_log(
                self.db,
                action="security.token_reuse_detected",
                user_id=uuid.UUID(user_id),
                description="Revoked refresh token reused, all tokens revoked",
            )
            raise TokenReuseDetectedError()

        # Revoke old token
        stored_token.revoked = True

        # Create new tokens
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one()
        access_token = create_access_token(user.id, user.role.name, user.role.permissions)
        new_refresh_jwt, new_jti = create_refresh_token(user.id)

        # Store new refresh token hash
        new_rt = RefreshToken(
            token_hash=hash_token_jti(new_jti),
            user_id=user.id,
            expires_at=datetime.now(UTC) + __import__("datetime").timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.db.add(new_rt)
        await self.db.flush()

        await write_audit_log(
            self.db,
            action="user.token_refreshed",
            user_id=user.id,
        )

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_jwt,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def logout(self, refresh_jwt: str, user_id: uuid.UUID) -> None:
        """Invalidate a refresh token."""
        try:
            payload = decode_token(refresh_jwt)
        except JWTError:
            return  # Silent fail on logout for invalid tokens

        jti = payload.get("jti")
        if not jti:
            return

        token_hash = hash_token_jti(jti)
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        stored = result.scalar_one_or_none()
        if stored:
            stored.revoked = True

        await write_audit_log(
            self.db,
            action="user.logout",
            user_id=user_id,
            description="User logged out",
        )
        await self.db.flush()

    async def get_current_user(self, token: str) -> User:
        """Decode access token and return the full User with role loaded."""
        try:
            payload = decode_token(token)
        except JWTError as e:
            if "expired" in str(e).lower():
                raise TokenExpiredError() from None
            raise InvalidTokenError() from None

        if payload.get("type") != "access":
            raise InvalidTokenError()

        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenError()

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise InvalidTokenError()

        if not user.is_active:
            raise AccountDisabledError()

        return user

    async def _revoke_all_user_tokens(self, user_id: uuid.UUID) -> None:
        """Revoke all refresh tokens for a user."""
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(revoked=True)
        )
        await self.db.flush()

    async def revoke_all_user_tokens(self, user_id: uuid.UUID) -> None:
        """Public method to revoke all refresh tokens."""
        await self._revoke_all_user_tokens(user_id)


def _user_profile(user: User) -> dict:
    """Convert a User ORM object to a profile dict."""
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

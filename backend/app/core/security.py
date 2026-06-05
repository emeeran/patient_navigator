"""Security utilities: password hashing and JWT token management."""

import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import jwt

from app.core.config import settings


def hash_password(plain: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: str, role: str, permissions: dict) -> str:
    """Create a JWT access token (30-minute expiry)."""
    expires = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "permissions": permissions,
        "exp": expires,
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> tuple[str, str]:
    """Create a JWT refresh token (7-day expiry). Returns (token, jti)."""
    jti = str(uuid.uuid4())
    expires = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "exp": expires,
        "type": "refresh",
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token. Raises JWTError on invalid/expired."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def hash_token_jti(jti: str) -> str:
    """Hash a JTI claim for storage in refresh_tokens table."""
    return hashlib.sha256(jti.encode()).hexdigest()

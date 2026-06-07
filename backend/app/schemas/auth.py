"""Pydantic schemas for authentication endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.schemas.validators import check_at_least_one, check_password_complexity

# ── Request schemas ───────────────────────────────────

ROLE_PATTERN = r"^(admin|navigator|clinician|volunteer|patient)$"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password: min 8 chars, upper, lower, digit, special",
    )
    full_name: str = Field(..., min_length=1, max_length=255)
    phone: str | None = Field(None, max_length=20)
    role: str = Field(..., pattern=ROLE_PATTERN)

    @model_validator(mode="after")
    def validate_password_complexity(self):
        check_password_complexity(self.password)
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class UserUpdateRequest(BaseModel):
    role: str | None = Field(None, pattern=ROLE_PATTERN)
    is_active: bool | None = None
    full_name: str | None = Field(None, min_length=1, max_length=255)
    phone: str | None = Field(None, max_length=20)

    @model_validator(mode="after")
    def at_least_one_field(self):
        check_at_least_one(self, "role", "is_active", "full_name", "phone")
        return self


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, description="Current password for verification")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password: min 8 chars, upper, lower, digit, special",
    )

    @model_validator(mode="after")
    def validate_password_complexity(self):
        check_password_complexity(self.new_password)
        return self


class AdminResetPasswordRequest(BaseModel):
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password: min 8 chars, upper, lower, digit, special",
    )

    @model_validator(mode="after")
    def validate_password_complexity(self):
        check_password_complexity(self.new_password)
        return self


class UserProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    phone: str | None = Field(None, max_length=20)

    @model_validator(mode="after")
    def at_least_one_field(self):
        check_at_least_one(self, "full_name", "phone")
        return self


class ChangePasswordResponse(BaseModel):
    message: str = "Password changed successfully"


# ── Response schemas ──────────────────────────────────

class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    phone: str | None
    role: str
    permissions: dict
    is_active: bool
    last_login_at: datetime | None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfile


class UserListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    phone: str | None
    role: str
    is_active: bool
    last_login_at: datetime | None


class UserListResponse(BaseModel):
    items: list[UserListItem]
    total: int
    page: int
    limit: int
